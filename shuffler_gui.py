
import os
import random
import time
import csv
import tkinter as tk
from tkinter import messagebox

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

N = 16
CSV_NAME = "shuffle.csv"
SOUND_FILE = "randomizer.ogg"
SOUND_VOLUME = 0.9

def deranged_shuffle(n=N, max_tries=20000):
    base = list(range(1, n+1))
    best, best_score = None, float("inf")
    for _ in range(max_tries):
        perm = base[:]
        random.shuffle(perm)
        if any(perm[i] == base[i] for i in range(n)):
            continue
        pos = {val: idx for idx, val in enumerate(perm)}
        violations = sum(1 for k in range(1, n) if abs(pos[k] - pos[k+1]) == 1)
        if violations == 0:
            return perm
        if violations < best_score:
            best_score, best = violations, perm
    return best

def load_from_csv(base_dir):
    names = [str(i) for i in range(1, N+1)]
    perm = None
    path = os.path.join(base_dir, CSV_NAME)
    if not os.path.exists(path):
        return names, perm
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        if not rows:
            return names, perm
        header = [h.strip().lower() for h in rows[0]]
        pid_idx = header.index("permanentid") if "permanentid" in header else (header.index("id") if "id" in header else None)
        name_idx = header.index("name") if "name" in header else None
        pos_idx = next((header.index(k) for k in ("shuffledposition", "position", "pos") if k in header), None)
        if pid_idx is not None and name_idx is not None:
            for r in rows[1:]:
                if len(r) <= max(pid_idx, name_idx): continue
                try: pid = int(r[pid_idx])
                except: continue
                if 1 <= pid <= N:
                    nm = (r[name_idx] or "").strip()
                    names[pid-1] = nm if nm else str(pid)
        if pid_idx is not None and pos_idx is not None:
            pos_to_pid = {}
            for r in rows[1:]:
                if len(r) <= max(pid_idx, pos_idx): continue
                try: pid = int(r[pid_idx]); pos = int(r[pos_idx])
                except: continue
                if 1 <= pid <= N and 1 <= pos <= N:
                    pos_to_pid[pos] = pid
            if len(pos_to_pid) == N:
                perm = [pos_to_pid[i+1] for i in range(N)]
    except: pass
    return names, perm

def save_to_csv(base_dir, names, current_perm):
    path = os.path.join(base_dir, CSV_NAME)
    header = ["PermanentID", "Name", "ShuffledPosition", "NameAtPosition"]
    id_to_pos = {pid: pos+1 for pos, pid in enumerate(current_perm)}
    rows = [header]
    for pid in range(1, N+1):
        name = names[pid-1]
        pos = id_to_pos.get(pid, "")
        name_at_pos = names[current_perm[pos-1]-1] if isinstance(pos, int) and 1 <= pos <= N else ""
        rows.append([pid, name, pos, name_at_pos])
    with open(path, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)

def play_click_sound(base_dir):
    path = os.path.join(base_dir, SOUND_FILE)
    if not os.path.exists(path):
        path = os.path.join(os.getcwd(), SOUND_FILE)
        if not os.path.exists(path):
            return False
    try:
        import pygame # type: ignore
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.music.set_volume(SOUND_VOLUME)
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        return True
    except Exception:
        return False

class ShufflerGUI:
    def __init__(self, root):
        self.root = root
        root.title("Red Tails Seat Shuffler")
        self.ids = list(range(1, N+1))
        self.current_perm = self.ids[:]
        self.animating = False
        self.animation_start = None
        self.animation_duration = 3.65
        self.animation_interval_ms = 100
        try:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            self.base_dir = os.getcwd()
        self.names, perm_from_csv = load_from_csv(self.base_dir)
        if perm_from_csv and len(perm_from_csv) == N:
            self.current_perm = perm_from_csv[:]
        tk.Label(root, text="Name / Seat", font=("TkDefaultFont", 11, "bold")).grid(row=0, column=0, padx=8, pady=6)
        tk.Label(root, text="Shuffled POSITION (1–16)", font=("TkDefaultFont", 11, "bold")).grid(row=0, column=1, padx=8, pady=6)
        self.name_entries, self.right_labels = [], []
        for i in range(N):
            e = tk.Entry(root, width=18, relief="groove", justify="center")
            e.insert(0, self.names[i])
            e.grid(row=i+1, column=0, padx=4, pady=2, sticky="nsew")
            self.name_entries.append(e)
            lbl = tk.Label(root, text="", width=18, relief="groove")
            lbl.grid(row=i+1, column=1, padx=4, pady=2, sticky="nsew")
            self.right_labels.append(lbl)
        self._update_right_labels_positions(self.current_perm)
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=N+1, column=0, columnspan=2, pady=(10,6))
        self.shuffle_btn = tk.Button(btn_frame, text="Shuffle", command=self.start_shuffle_animation, width=14)
        self.shuffle_btn.pack(side="left", padx=6)
        self.save_btn = tk.Button(btn_frame, text="Save CSV", command=self.save_csv, width=14)
        self.save_btn.pack(side="left", padx=6)
        self.status = tk.Label(root, text="Left: names. Right: each name's POSITION. \nSeat 5 shows CURSED SEAT (CSV stays numeric 5).", fg="gray")
        self.status.grid(row=N+2, column=0, columnspan=2, pady=(4,10))
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        self._audio_warned = False

    def start_shuffle_animation(self):
        if self.animating:
            return
        self.names = [e.get().strip() or str(i+1) for i, e in enumerate(self.name_entries)]
        ok = play_click_sound(self.base_dir)
        if not ok and not self._audio_warned:
            self.status.config(text="No in-app audio backend. pip install pygame for seamless sound.")
            self._audio_warned = True
        self.animating = True
        self.animation_start = time.time()
        self.shuffle_btn.config(state="disabled")
        self.status.config(text="Scrambling…")
        self._tick_animation()

    def _tick_animation(self):
        elapsed = time.time() - self.animation_start
        if elapsed < self.animation_duration:
            perm = self.ids[:]
            random.shuffle(perm)
            self._update_right_labels_positions(perm)
            if random.random() < 0.25:
                i, j = random.sample(range(N), 2)
                perm[i], perm[j] = perm[j], perm[i]
                self._update_right_labels_positions(perm)
            self.root.after(self.animation_interval_ms, self._tick_animation)
        else:
            final = deranged_shuffle(N)
            self.current_perm = final
            self._update_right_labels_positions(final)
            self.animating = False
            self.shuffle_btn.config(state="normal")
            score = self._adjacency_violations(final)
            if score == 0:
                self.status.config(text="Shuffle complete!")
            else:
                self.status.config(text=f"Done. {score} adjacency violation(s) minimized.")

    def _update_right_labels_positions(self, perm):
        id_to_pos = {pid: pos+1 for pos, pid in enumerate(perm)}
        for row_idx in range(N):
            pid = row_idx + 1
            pos = id_to_pos.get(pid, "")
            if pos == 5:
                self.right_labels[row_idx].config(text="CURSED SEAT (5)", fg="darkred")
            else:
                self.right_labels[row_idx].config(text=str(pos), fg="black")

    def _adjacency_violations(self, perm):
        # Count how many pairs of consecutive IDs are adjacent in the permutation
        pos = {val: idx for idx, val in enumerate(perm)}
        return sum(1 for k in range(1, N) if abs(pos[k] - pos[k+1]) == 1)

    def save_csv(self):
        try:
            save_to_csv(self.base_dir, self.names, self.current_perm)
            messagebox.showinfo("Saved", f"Saved to:\n{os.path.join(self.base_dir, CSV_NAME)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save CSV:\n{e}")

def main():
    root = tk.Tk()
    ShufflerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
