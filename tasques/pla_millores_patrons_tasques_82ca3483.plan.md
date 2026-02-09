---
name: Pla millores patrons tasques
overview: Crear un document markdown a la carpeta tasques que descrigui un pla de millores del codi mitjançant patrons de disseny, seguint l'estil dels documents existents (REFACTORITZACIO_FASE1.md, ANALISI_TASQUES.md).
todos: []
isProject: false
---

# Pla: document de millores amb patrons a tasques/

## Objectiu

Crear un fitxer **[tasques/PLA_MILLORES_PATRONS.md](tasques/PLA_MILLORES_PATRONS.md)** que reculli un pla de millores del codi aplicant patrons de disseny, amb prioritat, esforç i passos concretes, en el mateix to que [tasques/REFACTORITZACIO_FASE1.md](tasques/REFACTORITZACIO_FASE1.md).

## Estructura proposada del document

1. **Títol i introducció**
  Títol tipus "Pla de millores amb patrons de disseny" i un breu paràgraf que situï l’objectiu (millorar mantenibilitat, testabilitat i desacoblament de [gpt_car.py](gpt_car.py) i mòduls relacionats).
2. **Resum / diagrama de context**
  Diagrama Mermaid opcional (flowchart o C4 simplificat) que mostri les capes actuals (entrada, orquestració, serveis, hardware) i on s’aplicarien els patrons.
3. **Patrons per tasca**
  Per a cada millora, una secció amb:
  - **Prioritat** (Alta / Mitjana / Baixa)
  - **Esforç** (Baix / Mitjà / Alt)
  - **Impacte** (Mantenibilitat, Testabilitat, Desacoblament, etc.)
  - **Descripció** del problema actual i del patró
  - **Fitxers afectats** (gpt_car.py, preset_actions.py, etc.)
  - **Passos** o proposta concreta (sense codi exhaustiu si no cal, o amb fragments mínims com a [REFACTORITZACIO_FASE1.md](tasques/REFACTORITZACIO_FASE1.md))
  - **Beneficis** esperats
4. **Ordre d’implementació recomanat**
  Llista numerada de tasques en l’ordre suggerit (p. ex. configuració i injecció de dependències primer; facade i strategy després; observer/state si s’amplia).
5. **Referències**
  Enllaços breus a AGENTS.md, mòduls principals i, si s’escau, a documentació externa dels patrons.

## Contingut per patró (tasques a incloure al .md)

Basat en l’anàlisi previa del codi:


| #   | Patró / millora                                      | Prioritat | Esforç | Fitxers principals            |
| --- | ---------------------------------------------------- | --------- | ------ | ----------------------------- |
| 1   | Objecte de configuració (dataclass o dict de config) | Alta      | Baix   | gpt_car.py                    |
| 2   | Injecció de dependències a main() / orquestrador     | Alta      | Mitjà  | gpt_car.py                    |
| 3   | Strategy per a l’input (veu vs teclat)               | Mitjana   | Baix   | gpt_car.py                    |
| 4   | Facade per al cas d’ús "processar consulta"          | Mitjana   | Mitjà  | gpt_car.py                    |
| 5   | Observer / events o Queue per desacoblar threads     | Mitjana   | Alt    | gpt_car.py                    |
| 6   | State explícit per action_status i LED               | Baixa     | Mitjà  | gpt_car.py                    |
| 7   | Command (opcional) per a accions                     | Baixa     | Mitjà  | preset_actions.py, gpt_car.py |


Cada tasca al document ha d’explicar breument el problema actual (amb referència a funcions o línies rellevants), el patró a aplicar i els passos d’implementació en forma de llista.

## Acció única

- **Crear** el fitxer [tasques/PLA_MILLORES_PATRONS.md](tasques/PLA_MILLORES_PATRONS.md) amb el contingut descrit (títol, introducció, diagrama opcional, seccions per patró amb prioritat/esforç/impacte/descripció/fitxers/passos/beneficis, ordre d’implementació i referències).

No es modifica cap altre fitxer del projecte; només s’afegeix aquest document de pla a la carpeta tasques.