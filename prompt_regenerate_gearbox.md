# Prompt na znovuvygenerovanie modelu prevodovky miešača (v4)

Vytvor parametrický OpenSCAD model (BOSL2) prevodovky pre automatický miešač v hrnci:

- Dvojica priamozubých kužeľových kolies (`bevel_gear`, spiral=0), uhol hriadeľov 30° (vstup odklonený 30° od zvislice), modul 2, pastorok 15 zubov, výstupné koleso 29 zubov, backlash 0.2.
- Vstup: 6 mm hriadeľ prichádza od motora zdola pod 30° od zvislice. Výstup: 6 mm hriadeľ zvislo dolu do hrnca.
- Každý hriadeľ v dvoch ložiskách 626 (6×19×6) vzdialených od seba 18 mm; lôžka ložísk Ø19.3 × 6.4 mm (vôľa na tlač), osadenie drží iba vonkajší krúžok. Medzi kolesom a horným ložiskom tenká podložka Ø8.4 × 2.7 mm (tlačí len na vnútorný krúžok ložiska, nie na krytku).
- Kolesá: plochý chrbát (cone_backing=false), M3 červík radiálne + zapustená M3 matica otvorená zo zadnej strany. Výška zubov nad pätnou kružnicou = face_width·cos(pitch_angle) + 1 mm; dutina puzdra o 2.5 mm vyššia.
- Axiálna zarážka: na čele každého kolesa náboj Ø12 okolo otvoru, siahajúci do výšky zubov; oproti nemu na stene puzdra podložka Ø14 s medzerou 0.3 mm. Pri posune kolesa sa musí dotknúť len náboj a podložka, nikdy zuby.
- Puzdro: delené na dve polovice v rovine oboch hriadeľov, obrys = hull okolo oboch kolies + rúrky pre ložiská, steny 3 mm. Spojenie M3 skrutkami cez obvodovú prírubu (hlava na jednej strane, šesťhranná matica na druhej). Príruba končí zarovno s koncom rúrok, aby nezakrývala výstup hriadeľov.
- Uchytenie: žiadna montáž navrchu. Na vonkajšej strane vstupnej rúrky (od hrnca preč) je uchytenie dreveného ramena 20×40 mm postaveného na hranu (40 mm v rovine hriadeľov, kde ho ohýba váha), rovnobežného so vstupným hriadeľom; bližšia plocha ramena je 31.5 mm od osi vstupu (polomer skľučovadla Ø55 na motore + 4 mm vôľa). Rozmery ramena, uhol a skrutky sú spoločné v `common.scad`. Rameno nie je obalené: každá polovica puzdra má jednu plochú líčnicu (6 mm) priloženú k boku ramena, dĺžka 40 mm, a navrchu stropík 4 mm ako doraz (váha ide do čela ramena, nie do skrutiek). Na každej líčnici 2 zapustené skrutky do dreva 4 mm, na druhej strane zrkadlovo posunuté, aby sa v dreve nestretli.
- Výstupy cez premennú `part`: assembly (rez), housing_a, housing_b, gear_out, gear_in, spacer – diely uložené na tlač (polovice deliacou plochou dolu).
- Over, že sa kolesá nepretínajú navzájom ani s puzdrom, že pri axiálnom posune o 0.4 mm sa dotýka iba náboj, a exportuj STL.
