# Ringo Smart Lock Integration for Home Assistant

**Ringo integracija** omogoča avtomatizacijo **generiranja, urejanja in brisanja ključev**, uporabo ključavnic (zaklepanje/odklepanje) neposredno iz **Home Assistanta** in še veliko več.

## ⚙️ Zahteve

- Nameščen Home Assistant (priporočena zadnja stabilna različica)
- **Ringo API client ID in secret**, ki ju pridobite tako, da kontaktirate podjetje **Ringo**

## 🚀 Ključne funkcionalnosti

- Zaklepanje in odklepanje ključavnic iz Home Assistanta
- Ustvarjanje, urejanje in brisanje dostopnih ključev
- Nastavitve časa samodejnega zaklepanja
- Podpora več ključavnic hkrati

## 📦 Namestitev

1. **Prenesi integracijo:**
   - Z ukazom:
     ```bash
     git clone https://github.com/ime-uporabnika/ringo-smart-lock-integration.git
     ```
     ali
   - Prenesi `.zip` datoteko iz GitHub in jo razširi.

2. **Kopiraj datoteke:**
   - Vsebino mape `src/` kopiraj v:
     ```
     config/custom_components/ringo/
     ```

3. **Znova zaženi Home Assistant.**

4. **Dodaj integracijo prek Home Assistant vmesnika:**
   - Vnesti bo treba:
     - Ringo API **client ID**
     - Ringo API **secret**
     - Trajanje, za koliko časa naj se ključavnica odpre

