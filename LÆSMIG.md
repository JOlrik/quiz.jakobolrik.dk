# Quiz-sitet (quiz.jakobolrik.dk)

Dine gamle produkt-quizzer fra GoOnlive, sat op som et lille website uden server og uden database.
Alt ligger som almindelige filer i mappen `site/`, og den mappe kan lægges på en gratis host (Netlify, Cloudflare Pages eller GitHub Pages).

## Sådan virker det
- Forsiden viser de 12 quizzer, der var aktive på den gamle platform.
- Hver quiz har sin egen side. Spørgsmålene kommer ét ad gangen, og pointene tælles på samme måde som før: Det resultat, der får flest point, vinder.
- Hvert resultat har sin egen side med sit eget billede. Det er den side, folk deler på Facebook, så opslaget viser fx "Mit resultat: Ild".
- Når en ven klikker på opslaget, ser vennen resultatet og en knap til at tage testen selv.
- Under hvert resultat er der en boks med link til det kursus, quizzen hører til.

## Ændringer
Alt styres fra `indstillinger.json`:
- `adresse`: den adresse, sitet skal ligge på. Facebook skal bruge den til billederne.
- `kurser`: link til hvert kursus og en eventuel `rabatkode`. Koden vises under resultatet, hvis den er udfyldt. Koden skal først oprettes i Squarespace.
- `skjult`: quizzer, der er bygget, men ikke står på forsiden. Man kan stadig nå dem via deres link.
- `udeladt`: quizzer, der slet ikke bygges, og hvorfor.

Spørgsmål, svar og resultattekster står i `data/quizzer.json`.

Efter en ændring bygges sitet igen med:

    python3 byg.py

## Filer
- `byg.py`: bygger `site/`
- `skabelon/style.css` og `skabelon/quiz.js`: udseende og quizmotor
- `fonts/`: Instrument Serif og DM Sans (fri licens, OFL) til delebillederne
- `site/`: det færdige site, der skal lægges online

## Tekstsvar

`data/tekstsvar.json` giver spørgsmål nye tekster, hvor svarene stod på billeder, der er gået tabt. Pointene er uændrede.
