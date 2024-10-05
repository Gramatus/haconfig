# Legg til eller flytt lys

> Merk: programvaren under er basert på "v1"-api'et til Hue som egentlig er deprecated

* Programvare: https://github.com/Gramatus/HueConfigApp
* Data: Dropbox\Konfigurasjonsfiler\MySceneDefinitions.xlsx

I arket `SceneDefinitions` finnes kolonnen `lights` som angir hvilke lys som inngår i hvilke scener. Dette må oppdateres for å få riktig resultat.

Programmet leser data fra en CSV-fil basert på dette arket. Se i `Program.cs` etter `configFolder` og `transitionRulesDefsFile`. Skal være `Dropbox\Konfigurasjonsfiler\HueConfig\TransitionScenedefs.csv`.

> Merk: CSV-filen er lagret med `windows 1252`-encoding!

## Eksempel

> lys#6 er ikke lenger brukt i transitions, men lys#62 skal inn.

* Det enkleste her er å bytte 6 med 62 i kolonnen `lights`. For å legge til eller fjerne lys omtrent samme, bare litt mer jobb siden vi ikke har en replace-støtte.
* Regnearket skal ha filter på `Aktiv: ja` og `Formål: Transition`
* Åpne CSV-filen og slett alt unntatt overskriftene
* Gå tilbake til regnearket, kopier hele tabellen (som er filtrert) med overskrifter
* Lim inn i CSV-filen som ren tekst.
* Sjekk at overskriftene er de samme, slett første rad.
* Lagre CSV-filen.
* Sjekk `Progam.cs` og finn `#region Select what to do`. Sjekk at alt er `false` utenom `bool updateTransitionScenesOnly = true;`.
* Run `debug.bat`.

# Få data fra bridge

> Api-nøkkelen ligger i Google Passordlagring under `hue_bridge.local`. Kan også generere en ny via Hue Bridge ved behov, se [Hue API V2: Getting started](https://developers.meethue.com/develop/hue-api-v2/getting-started/). Nøkkelen er samme for v1 og v2.

```sh
./read_hue.sh -t <api_Key> -a scenes
./read_hue.sh -t <api_Key> -a scenes -r PlnpsZgSQpM4Wuf
./read_hue.sh -t <api_Key> -a lights
```
