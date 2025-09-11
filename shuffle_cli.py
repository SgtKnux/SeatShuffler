import os
import csv
import random
import argparse
import time

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

def load_from_csv(path):
    names = [str(i) for i in range(1, N+1)]
    perm = None
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
        pos_idx = next((header.index(k) for k in ("shuffledposition","position","pos") if k in header), None)
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
                try:
                    pid = int(r[pid_idx]); pos = int(r[pos_idx])
                except:
                    continue
                if 1 <= pid <= N and 1 <= pos <= N:
                    pos_to_pid[pos] = pid
            if len(pos_to_pid) == N:
                perm = [pos_to_pid[i+1] for i in range(N)]
    except Exception:
        pass
    return names, perm

def save_to_csv(path, names, current_perm):
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

def adjacency_violations(perm):
    pos = {val: idx for idx, val in enumerate(perm)}
    return sum(1 for k in range(1, N) if abs(pos[k] - pos[k+1]) == 1)

def play_sound(base_dir, sound_file=SOUND_FILE, volume=SOUND_VOLUME):
    path = os.path.join(base_dir, sound_file)
    if not os.path.exists(path):
        return False
    try:
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        import pygame  # type: ignore
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        # brief wait so short sounds are audible in CLI runs
        t0 = time.time()
        while pygame.mixer.music.get_busy() and (time.time() - t0) < 5:
            time.sleep(0.05)
        return True
    except Exception:
        return False

def main():
    ap = argparse.ArgumentParser(description="Shuffle 1–16, load/save CSV compatible with web app.")
    ap.add_argument("--csv", default=CSV_NAME, help="CSV path (default: shuffle.csv)")
    ap.add_argument("--shuffle", action="store_true", help="Perform a new shuffle and save")
    ap.add_argument("--sound", action="store_true", help="Play randomizer.ogg if available (pygame)")
    args = ap.parse_args()

    base_dir = os.getcwd()
    csv_path = os.path.join(base_dir, args.csv)

    names, perm = load_from_csv(csv_path)
    if perm and len(perm) == N:
        current_perm = perm[:]
    else:
        current_perm = list(range(1, N+1))

    if args.shuffle:
        if args.sound:
            play_sound(base_dir)
        final = deranged_shuffle(N)
        current_perm = final
        save_to_csv(csv_path, names, current_perm)
        print(f"Saved new shuffle to {csv_path}")
        print(f"Adjacency violations: {adjacency_violations(final)}")
    else:
        # Just echo current mapping
        if perm:
            print("Existing positions from CSV:")
        else:
            print("No positions found; identity mapping:")
        id_to_pos = {pid: pos+1 for pos, pid in enumerate(current_perm)}
        for pid in range(1, N+1):
            nm = names[pid-1]
            pos = id_to_pos.get(pid, "")
            print(f"{pid:>2}: {nm:<20} -> {pos}")

if __name__ == "__main__":
    main()
