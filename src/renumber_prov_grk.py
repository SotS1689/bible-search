"""
One-off fix: CATSS/Rahlfs LXX Proverbs relocates Hebrew chapters 25-29
("these also are proverbs of Solomon, which the men of Hezekiah...
copied out") as a block to the end of the Greek book, after chs 30
(Agur) and 31 (Lemuel) -- so the raw .mlxx import tagged that block
under its native Greek chapter numbers, 32-36, verse numbers unchanged.
That left Greek chapters 25-29 empty and 32-36 as orphaned extras, which
the reading view has no reason to show under different numbers than
Hebrew/English -- so this renumbers that block back to 25-29 in place,
matching every other book, rather than remapping it at display time.
(Contrast Jeremiah 25-51, whose LXX reordering has no clean 1:1 chapter
correspondence and is instead remapped at display time by
static/js/versification.js.)

Run once, against an existing corpus.db:
    python src/renumber_prov_grk.py [path-to-corpus.db]
"""
import sqlite3, sys

BOOK_PROVERBS = 20


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/corpus.db'
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    cur.execute(
        "SELECT chapter, count(*) FROM words "
        "WHERE book=? AND lang='grk' AND chapter BETWEEN 25 AND 29 "
        "GROUP BY chapter", (BOOK_PROVERBS,))
    existing = cur.fetchall()
    if existing:
        raise SystemExit(f"Refusing to overwrite existing Grk Prov 25-29 rows: {existing}")

    cur.execute(
        "UPDATE words SET chapter = chapter - 7 "
        "WHERE book=? AND lang='grk' AND chapter BETWEEN 32 AND 36",
        (BOOK_PROVERBS,))
    print(f"renumbered {cur.rowcount} rows (Grk Prov 32-36 -> 25-29)")
    con.commit()
    con.execute('VACUUM')
    con.close()


if __name__ == '__main__':
    main()
