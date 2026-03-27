import time
import random
import functools


# ===================== ДЕКОРАТОР ДЛЯ ЗАМЕРА ВРЕМЕНИ =======================
def timer(func):
    @functools.wraps(func)
    def wrapper(arr, *args, **kwargs):
        start = time.time()
        result = func(arr, *args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed
    return wrapper


# ===================== СОРТИРОВКА МЕТОДОМ BUBBLE SORT =======================
@timer
def bubble_sort(arr):
    arr_copy = arr.copy()
    n = len(arr_copy)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            if arr_copy[j] > arr_copy[j + 1]:
                arr_copy[j], arr_copy[j + 1] = arr_copy[j + 1], arr_copy[j]
                swapped = True
        if not swapped:
            break
    return arr_copy


# ===================== СОРТИРОВКА МЕТОДОМ SELECTION SORT =======================
@timer
def selection_sort(arr):
    arr_copy = arr.copy()
    n = len(arr_copy)
    for i in range(n):
        min_index = i
        for j in range(i + 1, n):
            if arr_copy[j] < arr_copy[min_index]:
                min_index = j
        arr_copy[i], arr_copy[min_index] = arr_copy[min_index], arr_copy[i]
    return arr_copy


# ===================== СОРТИРОВКА МЕТОДОМ SHELL SORT =======================
@timer
def shell_sort(arr):
    arr_copy = arr.copy()
    n = len(arr_copy)
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            temp = arr_copy[i]
            j = i
            while j >= gap and arr_copy[j - gap] > temp:
                arr_copy[j] = arr_copy[j - gap]
                j -= gap
            arr_copy[j] = temp
        gap //= 2
    return arr_copy


# ===================== СОРТИРОВКА МЕТОДОМ QUICK SORT =======================
@timer
def quick_sort(arr):
    def _quick_sort(arr):
        if len(arr) <= 1:
            return arr
        pivot = arr[len(arr) // 2]
        left = [x for x in arr if x < pivot]
        middle = [x for x in arr if x == pivot]
        right = [x for x in arr if x > pivot]
        return _quick_sort(left) + middle + _quick_sort(right)
    return _quick_sort(arr.copy())


# ===================== СОРТИРОВКА МЕТОДОМ INSERT SORT =======================
@timer
def insert_sort(arr):
    arr_copy = arr.copy()
    n = len(arr_copy)
    for i in range(1, n):
        elem = arr_copy[i]
        j = i
        while j >= 1 and arr_copy[j - 1] > elem:
            arr_copy[j] = arr_copy[j - 1]
            j -= 1
        arr_copy[j] = elem
    return arr_copy


# ===================== ТЕСТИРОВАНИЕ СПИСКОВ =======================
# Списки для тестирования
test_lists = {
    10: [random.randint(1, 100) for _ in range(10)],
    30: [random.randint(1, 100) for _ in range(30)],
    50: [random.randint(1, 100) for _ in range(50)],
    90: [random.randint(1, 100) for _ in range(90)],
    100: [random.randint(1, 1000) for _ in range(100)],
    500: [random.randint(1, 1000) for _ in range(500)],
}

algorithms = [
    ("Пузырьковая", bubble_sort),
    ("Выбором", selection_sort),
    ("Вставками", insert_sort),
    ("Шелла", shell_sort),
    ("Быстрая", quick_sort),
]

print("=" * 115)
print(
    f"{'АЛГОРИТМ':^11} | {'10 эл.':^14} | {'30 эл.':^14} | {'50 эл.':^14} | {'90 эл.':^14} | {'100 эл.':^14} | "
    f"{'500 эл.':^14}")
print("=" * 115)


for algo_name, algo_func in algorithms:
    results = []
    sizes = sorted(test_lists.keys())

    for size in sizes:
        test_list = test_lists[size]

        # Пропускаем медленные алгоритмы на больших данных
        if algo_name in ["Пузырьковая", "Выбором", "Вставками"] and size > 100:
            results.append("слишком медленно")
        else:
            try:
                sorted_result, elapsed = algo_func(test_list)
                results.append(f"{elapsed:^9.6f} сек.")
            except Exception as e:
                results.append(f"ошибка")
                print(f"  Ошибка в {algo_name} на размере {size}: {e}")

    print(
        f"{algo_name:<11} | {results[0]:^12} | {results[1]:^12} | {results[2]:^12} | {results[3]:^12} | "
        f"{results[4]:^12} | {results[5]:^12}")

print("=" * 115)

# ===================== ВЫВОД РЕЗУЛЬТАТОВ СОРТИРОВКИ =======================
print("\n" + "=" * 55)
print("РЕЗУЛЬТАТЫ СОРТИРОВКИ для маленьких списков")
print("=" * 55)

small_sizes = [10, 30]
for size in small_sizes:
    print(f"\n▶ {size} элементов:")
    test_list = [random.randint(1, 100) for _ in range(size)]

    for algo_name, algo_func in algorithms:
        try:
            result, elapsed = algo_func(test_list.copy())
            print(f"  {algo_name:<12} | Время: {elapsed:^9.6f} сек. | {result}")
        except Exception as e:
            print(f"  {algo_name:12}: ошибка - {e}")

# ===================== ВЫВОДЫ =======================

width = 92 # Ширина рамки

print("\n" + "╔" + "═" * width + "╗")
print(f"║{'ВЫВОДЫ':^{width}}║")
print("╠" + "═" * width + "╣")

print(f"║ {'- Для больших списков (> 100 элементов) — лучше использовать БЫСТРУЮ СОРТИРОВКУ.':<{width-1}}║")
print(f"║ {'- Для средних списков (50-100 элементов) — можно использовать БЫСТРУЮ СОРТИРОВКУ и ШЕЛЛА.':<{width-1}}║")
print(f"║ {'- Для маленьких списков (< 50 элементов) — подходит ЛЮБАЯ сортировка.':<{width-1}}║")
print(f"║ {'- Для очень маленьких (< 10 элементов) — можно использовать сортировку ВСТАВКАМИ.':<{width-1}}║")
print(f"║ {'- Пузырьковая сортировка и сортировка Выбором — только для учебы (медленные).':<{width-1}}║")

print("╚" + "═" * width + "╝")


