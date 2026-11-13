import argparse
import json
import sys


def muat_kb(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fakta_dasar(kb):
    """Fakta yang tidak pernah menjadi hasil aturan -> ditanyakan ke user (urut kemunculan)."""
    hasil = {r["maka"] for r in kb["aturan"]}
    dasar = []
    for r in kb["aturan"]:
        for f in r["jika"]:
            if f not in hasil and f not in dasar:
                dasar.append(f)
    return dasar


def syarat_terpenuhi(aturan, memori):
    if aturan["mode"] == "dan":
        return all(f in memori for f in aturan["jika"])
    return any(f in memori for f in aturan["jika"])


def forward_chaining(kb, fakta_awal):
    memori = set(fakta_awal)
    asal = {}
    log = []
    siklus = 0
    while True:
        cocok = [r for r in kb["aturan"]
                 if r["maka"] not in memori and syarat_terpenuhi(r, memori)]
        if not cocok:
            siklus += 1
            log.append(f"Siklus {siklus}: tidak ada aturan baru, berhenti")
            break
        r = cocok[0]
        siklus += 1
        memori.add(r["maka"])
        asal[r["maka"]] = r
        log.append(f"Siklus {siklus}: {r['id']} -> {r['maka']}")
    return memori, asal, log


def kesimpulan_akhir(kb, asal):
    """Kesimpulan akhir = hasil aturan yang tidak dipakai sebagai syarat aturan lain."""
    dipakai = {f for r in kb["aturan"] for f in r["jika"]}
    return [f for f in asal if f not in dipakai]


def cetak_alasan(fakta, asal, memori, indent=1):
    r = asal.get(fakta)
    if r is None:
        return
    terpenuhi = [f for f in r["jika"] if f in memori]
    print("  " * indent + f"{fakta}  <- {r['id']} ({', '.join(terpenuhi)}) [{r['sumber']}]")
    for f in terpenuhi:
        cetak_alasan(f, asal, memori, indent + 1)


def tanya(pertanyaan_list):
    jawaban = []
    print("Jawab y/t.")
    for i, f in enumerate(pertanyaan_list, 1):
        while True:
            j = input(f"{i}. Apakah {f}? (y/t) > ").strip().lower()
            if j in ("y", "t"):
                break
        if j == "y":
            jawaban.append(f)
    return jawaban


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default="kb_lele.json")
    ap.add_argument("--ya", nargs="*", type=int, default=None,
                    help="nomor pertanyaan yang dijawab ya (mode otomatis)")
    args = ap.parse_args()

    kb = muat_kb(args.kb)
    dasar = fakta_dasar(kb)

    print(kb["judul"])
    if args.ya is None:
        fakta_awal = tanya(dasar)
    else:
        print("Mode otomatis. Pertanyaan:")
        fakta_awal = []
        for i, f in enumerate(dasar, 1):
            j = "y" if i in args.ya else "t"
            print(f"{i}. Apakah {f}? (y/t) > {j}")
            if j == "y":
                fakta_awal.append(f)

    print()
    print("Fakta awal:", ", ".join(fakta_awal) if fakta_awal else "(tidak ada)")
    print()

    memori, asal, log = forward_chaining(kb, fakta_awal)
    for baris in log:
        print(baris)
    print()

    akhir = kesimpulan_akhir(kb, asal)
    if akhir:
        print("Kesimpulan:", "; ".join(akhir))
        print("Alasan:")
        for k in akhir:
            cetak_alasan(k, asal, memori)
    else:
        print("Kesimpulan: tidak ada kesimpulan akhir dari fakta yang diberikan")
        antara = list(asal)
        if antara:
            print("Temuan antara:", "; ".join(antara))
    print()
    print("Catatan:", kb["batas"])


if __name__ == "__main__":
    sys.exit(main())
