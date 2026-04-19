import psycopg as psycopg2
import csv

DB_PARAMS = {
    "host": "localhost",
    "dbname": "lab7_db",
    "user": "postgres",
    "password": "6676",
    "port": "5432"
}


def get_conn():
    return psycopg2.connect(**DB_PARAMS)


# ══════════════════════════════════════════════
#  ЛАБ 7 
# ══════════════════════════════════════════════

def show_all():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM phonebook")
    rows = cur.fetchall()
    print("\n--- ТЕЛЕФОННАЯ КНИГА ---")
    for row in rows:
        print(f"Имя: {row[0]} | Тел: {row[1]}")
    cur.close()
    conn.close()


def add_contact():
    name = input("Введите имя: ")
    phone = input("Введите телефон: ")
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO phonebook (user_name, phone_number) VALUES (%s, %s)",
            (name, phone)
        )
        conn.commit()
        print("Контакт успешно добавлен!")
    except Exception as e:
        print(f"Ошибка при добавлении: {e}")
    finally:
        cur.close()
        conn.close()


def update_contact():
    name = input("Кому меняем номер? (Введите точное имя): ")
    new_phone = input("Введите новый телефон: ")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE phonebook SET phone_number = %s WHERE user_name = %s",
        (new_phone, name)
    )
    if cur.rowcount == 0:
        print(f"Ошибка: Контакт '{name}' не найден!")
    else:
        conn.commit()
        print("Успех: Номер обновлен!")
    cur.close()
    conn.close()


def delete_contact():
    name = input("Введите имя для удаления: ")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM phonebook WHERE user_name = %s", (name,))
    if cur.rowcount == 0:
        print(f"Ошибка: Контакт '{name}' не найден!")
    else:
        conn.commit()
        print("Контакт удален!")
    cur.close()
    conn.close()


def import_from_csv():
    try:
        conn = get_conn()
        cur = conn.cursor()
        with open('contacts.csv', mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  
            for row in reader:
                cur.execute(
                    "INSERT INTO phonebook (user_name, phone_number) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    row
                )
        conn.commit()
        print("Данные из CSV успешно загружены!")
        cur.close()
        conn.close()
    except FileNotFoundError:
        print("Ошибка: Файл contacts.csv не найден в папке c программой!")


# ══════════════════════════════════════════════
#  ЛАБ 8
# ══════════════════════════════════════════════

def search_by_pattern():
    """Поиск по части имени или номера телефона."""
    pattern = input("Введите часть имени или телефона для поиска: ")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM search_by_pattern(%s)", (pattern,))
    rows = cur.fetchall()
    print(f"\n--- Результаты поиска по '{pattern}' ---")
    if rows:
        for row in rows:
            print(f"Имя: {row[0]} | Тел: {row[1]}")
    else:
        print("Ничего не найдено.")
    cur.close()
    conn.close()


def upsert_user():
    """Добавить контакт или обновить телефон если уже существует."""
    name = input("Введите имя: ")
    phone = input("Введите телефон: ")
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("CALL upsert_user(%s, %s)", (name, phone))
        conn.commit()
        print("Готово!")
    except Exception as e:
        conn.rollback()
        print(f"Ошибка: {e}")
    finally:
        cur.close()
        conn.close()


def insert_many_users():
    """Массовая вставка: вводишь несколько контактов, неверные номера выводятся отдельно."""
    users = []
    print("Вводи контакты (имя и телефон). Чтобы закончить — введи пустое имя.")
    while True:
        name = input("  Имя (или Enter для завершения): ").strip()
        if not name:
            break
        phone = input("  Телефон: ").strip()
        users.append([name, phone])

    if not users:
        print("Список пустой, ничего не добавлено.")
        return

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("CALL insert_many_users(%s::VARCHAR[][], %s)", (users, None))
        result = cur.fetchone()
        conn.commit()
        invalid = result[0] if result else "Нет ошибок"
        print("\n--- Некорректные номера ---")
        print(invalid)
    except Exception as e:
        conn.rollback()
        print(f"Ошибка: {e}")
    finally:
        cur.close()
        conn.close()


def get_page():
    """Вывод записей постранично."""
    try:
        limit = int(input("Сколько записей на странице? "))
        page = int(input("Номер страницы (с 1)? "))
        offset = (page - 1) * limit
    except ValueError:
        print("Введи числа!")
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM get_phonebook_page(%s, %s)", (limit, offset))
    rows = cur.fetchall()
    print(f"\n--- Страница {page} (записей: {len(rows)}) ---")
    if rows:
        for row in rows:
            print(f"Имя: {row[0]} | Тел: {row[1]}")
    else:
        print("Больше записей нет.")
    cur.close()
    conn.close()


def delete_by_name_or_phone():
    """Удаление по имени или телефону."""
    print("Удалить по: 1 - имени  |  2 - телефону")
    choice = input("Выбор: ").strip()
    conn = get_conn()
    cur = conn.cursor()
    try:
        if choice == "1":
            name = input("Введите имя: ")
            cur.execute("CALL delete_user(%s, NULL)", (name,))
        elif choice == "2":
            phone = input("Введите телефон: ")
            cur.execute("CALL delete_user(NULL, %s)", (phone,))
        else:
            print("Неверный выбор.")
            return
        conn.commit()
        print("Готово!")
    except Exception as e:
        conn.rollback()
        print(f"Ошибка: {e}")
    finally:
        cur.close()
        conn.close()


# ══════════════════════════════════════════════
#  ГЛАВНОЕ МЕНЮ
# ══════════════════════════════════════════════

if __name__ == "__main__":
    while True:
        print("\n╔══════════════════════════════════╗")
        print("║       ТЕЛЕФОННАЯ КНИГА           ║")
        print("╠══════════════════════════════════╣")
        print("║  --- Лаб 7 ---                   ║")
        print("║  1. Показать все контакты        ║")
        print("║  2. Добавить контакт             ║")
        print("║  3. Обновить номер               ║")
        print("║  4. Удалить контакт              ║")
        print("║  5. Загрузить из CSV             ║")
        print("╠══════════════════════════════════╣")
        print("║  --- Лаб 8 ---                   ║")
        print("║  6. Поиск по паттерну            ║")
        print("║  7. Добавить / обновить (upsert) ║")
        print("║  8. Массовая вставка             ║")
        print("║  9. Постраничный вывод           ║")
        print("║  10. Удалить по имени/телефону   ║")
        print("╠══════════════════════════════════╣")
        print("║  0. Выход                        ║")
        print("╚══════════════════════════════════╝")

        choice = input("Выбери действие: ").strip()

        if   choice == "1":  show_all()
        elif choice == "2":  add_contact()
        elif choice == "3":  update_contact()
        elif choice == "4":  delete_contact()
        elif choice == "5":  import_from_csv()
        elif choice == "6":  search_by_pattern()
        elif choice == "7":  upsert_user()
        elif choice == "8":  insert_many_users()
        elif choice == "9":  get_page()
        elif choice == "10": delete_by_name_or_phone()
        elif choice == "0":
            print("Выход из программы")
            break
        else:
            print("Неверный ввод, попробуй еще раз.")
