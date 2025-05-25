# Ringo Smart Lock Integration for Home Assistant

**Ringo integracija** omogoča avtomatizacijo **generiranja, urejanja in brisanja ključev**, uporabo ključavnic (zaklepanje/odklepanje) neposredno iz **Home Assistanta** in še veliko več.

Integracija ima na voljo vse ključavnice kot locks, in jih lahko dodaš kot običajne ključavnice v Home Assistant, poleg tega pa ima na voljo services za ostale funkcionalnosti (create_key, update_key, delete_key, set_digital_key, get_locks, get_keys, get_users, get_key_status).

Povezava na YouTube posnetek, ki prikazuje delovanje integracije: https://youtu.be/3mL_Vg-DsCM

## ⚙️ Zahteve

- Nameščen Home Assistant (priporočena zadnja stabilna različica)
- **Ringo API client ID in secret**, ki ju pridobite tako, da kontaktirate podjetje **Ringo**

## 🚀 Ključne funkcionalnosti

- Zaklepanje in odklepanje ključavnic iz Home Assistanta
- Ustvarjanje, urejanje in brisanje dostopnih ključev
- Nastavitve časa samodejnega zaklepanja
- Podpora več ključavnic hkrati
- Services za upravljanje s ključi (create_key, update_key, delete_key, set_digital_key)
- Services za pridobivanje podatkov (get_locks, get_keys, get_users, get_key_status)

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

## 🔧 Uporaba

### Ključavnice kot naprave (Locks)

Integracija vse Ringo ključavnice doda v Home Assistant kot standardne ključavnice (locks). To pomeni, da jih lahko dodaš kot običajne ključavnice v Home Assistant in uporabljaš vsa standardna dejanja za ključavnice (lock/unlock).

### Dodatni servisi

Poleg standardnih funkcij ključavnic, integracija ponuja še dodatne servise za upravljanje s ključi in drugimi funkcionalnostmi:

### create_key
Ustvari nov dostopni ključ za določene ključavnice.

```yaml
service: ringo.create_key
data:
  name: "demonstracija key"
  times:
    - type: "date"
      start: 1671875935
      end: 1748753190
    - type: "schedule"
      start_time: "09:00:00"
      end_time: "13:00:00"
      monday: 1
      tuesday: 0
      wednesday: 1
      thursday: 0
      friday: 0
      saturday: 0
      sunday: 1
  locks:
    - lock_id: 295
      relay_id: 1
  use_pin: 0
```

### update_key
Posodobi obstoječi ključ.

```yaml
service: ringo.update_key
data:
  digital_key: "4cd2856a4fcd52c2b57ad47d2dcea7a9fb7f14a82d34e6532b2871208c6527a6"
  name: "posodobljen ključ"
  times:
    - type: "date"
      start: 1671875935
      end: 1748753190
  locks:
    - lock_id: 295
      relay_id: 1
  use_pin: 0
```

### delete_key
Izbriše obstoječi ključ.

```yaml
service: ringo.delete_key
data:
  digital_key: "4cd2856a4fcd52c2b57ad47d2dcea7a9fb7f14a82d34e6532b2871208c6527a6"
```

### set_digital_key
Nastavi digitalni ključ za določeno ključavnico.

```yaml
service: ringo.set_digital_key
data:
  entity_id: lock.front_door
  digital_key: "4cd2856a4fcd52c2b57ad47d2dcea7a9fb7f14a82d34e6532b2871208c6527a6"
```

### get_locks
Pridobi seznam vseh ključavnic.

```yaml
service: ringo.get_locks
```

### get_keys
Pridobi seznam vseh ključev.

```yaml
service: ringo.get_keys
data:
  lock_id: 295  # Opcijsko - če želiš pridobiti ključe samo za določeno ključavnico
```

### get_users
Pridobi seznam vseh uporabnikov.

```yaml
service: ringo.get_users
```

### get_key_status
Preveri status določenega ključa.

```yaml
service: ringo.get_key_status
data:
  digital_key: "4cd2856a4fcd52c2b57ad47d2dcea7a9fb7f14a82d34e6532b2871208c6527a6"
```

### Primer uporabe v avtomatizacijah

Servise lahko uporabiš tudi v avtomatizacijah Home Assistant. Primer JSON formata:

```yaml
action:
  service: ringo.create_key
  data: {"name":"demonstracija key","times":[{"type":"date","start":1671875935,"end":1748753190},{"type":"schedule","start_time":"09:00:00","end_time":"13:00:00","monday":1,"tuesday":0,"wednesday":1,"thursday":0,"friday":0,"saturday":0,"sunday":1}],"locks":[{"lock_id":295,"relay_id":1}],"use_pin":0}
```

Primer avtomatizacije za ustvarjanje ključa:

```yaml
automation:
  - alias: "Ustvari nov dostopni ključ ob obisku"
    trigger:
      platform: state
      entity_id: binary_sensor.visitor_arriving
      to: "on"
    action:
      service: ringo.create_key
      data:
        name: "Visitor Access"
        times:
          - type: "date"
            start: "{{ as_timestamp(now()) | int }}"
            end: "{{ as_timestamp(now() + timedelta(hours=4)) | int }}"
        locks:
          - lock_id: 295
            relay_id: 1
        use_pin: 0
```
