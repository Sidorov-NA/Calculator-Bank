import streamlit as st


# Расчет примерного НДФЛ с процентов за один расчетный год.
def calculate_tax(year_interest, tax_free_limit):
    tax_base = year_interest - tax_free_limit

    if tax_base < 0:
        tax_base = 0

    # Для учебной модели используются ставки 13% и 15%.
    if tax_base <= 2400000:
        tax = tax_base * 0.13
    else:
        tax = 2400000 * 0.13 + (tax_base - 2400000) * 0.15

    return tax


# Расчет накоплений за заданное количество месяцев.
def calculate_savings(initial_sum, monthly_payment, months,
                      annual_rate, inflation, tax_free_limit,
                      capitalization_months):
    balance = initial_sum
    own_money = initial_sum
    total_interest = 0
    pending_interest = 0
    year_interest = 0
    total_tax = 0

    monthly_rate = annual_rate / 100 / 12

    for month in range(1, months + 1):
        # Сначала начисляем проценты на текущий остаток.
        interest = balance * monthly_rate
        pending_interest = pending_interest + interest
        total_interest = total_interest + interest
        year_interest = year_interest + interest

        # Капитализируем проценты с выбранной периодичностью.
        if month % capitalization_months == 0:
            balance = balance + pending_interest
            pending_interest = 0

        # Пополнение вносится в конце месяца.
        balance = balance + monthly_payment
        own_money = own_money + monthly_payment

        # Для учебной модели налог оценивается за каждый период из 12 месяцев.
        if month % 12 == 0:
            total_tax = total_tax + calculate_tax(year_interest, tax_free_limit)
            year_interest = 0

    # Учитываем проценты за неполный последний год.
    if year_interest > 0:
        total_tax = total_tax + calculate_tax(year_interest, tax_free_limit)

    # При завершении срока учитываем уже начисленные, но еще не
    # капитализированные проценты.
    balance = balance + pending_interest

    after_tax = balance - total_tax
    if after_tax < 0:
        after_tax = 0

    years = months / 12
    real_value = after_tax / ((1 + inflation / 100) ** years)

    return {
        "own_money": own_money,
        "interest": total_interest,
        "before_tax": balance,
        "tax": total_tax,
        "after_tax": after_tax,
        "real_value": real_value,
        "years": years
    }


# Ищем количество месяцев, необходимое для достижения цели.
def find_months(initial_sum, monthly_payment, goal,
                annual_rate, inflation, tax_free_limit,
                capitalization_months):
    for months in range(1, 601):
        result = calculate_savings(
            initial_sum, monthly_payment, months,
            annual_rate, inflation, tax_free_limit,
            capitalization_months
        )

        if result["real_value"] >= goal:
            return months, result

    return None, None


# Ищем минимальное ежемесячное пополнение.
def find_monthly_payment(initial_sum, goal, months,
                         annual_rate, inflation, tax_free_limit,
                         capitalization_months):
    low = 0
    high = 1000

    # Сначала подбираем верхнюю границу для поиска.
    while high < 1000000000000:
        result = calculate_savings(
            initial_sum, high, months, annual_rate,
            inflation, tax_free_limit, capitalization_months
        )
        if result["real_value"] >= goal:
            break
        high = high * 2

    if high >= 1000000000000:
        return None

    # Постепенно уточняем результат до копеек.
    for step in range(40):
        middle = (low + high) / 2
        result = calculate_savings(
            initial_sum, middle, months, annual_rate,
            inflation, tax_free_limit, capitalization_months
        )

        if result["real_value"] >= goal:
            high = middle
        else:
            low = middle

    return high


# Ищем ставку, при которой получится достичь финансовой цели.
def find_rate(initial_sum, monthly_payment, goal, months,
              inflation, tax_free_limit, capitalization_months):
    low = 0
    high = 100

    result = calculate_savings(
        initial_sum, monthly_payment, months, high,
        inflation, tax_free_limit, capitalization_months
    )

    if result["real_value"] < goal:
        return None

    # Подбираем ставку в пределах от 0 до 100% годовых.
    for step in range(40):
        middle = (low + high) / 2
        result = calculate_savings(
            initial_sum, monthly_payment, months, middle,
            inflation, tax_free_limit, capitalization_months
        )

        if result["real_value"] >= goal:
            high = middle
        else:
            low = middle

    return high


# Переводим число в удобный вид с двумя знаками после запятой.
def rubles(value):
    return f"{value:,.2f}".replace(",", " ").replace(".", ",") + " руб."


# Выводим общий результат расчета.
def show_result(result, goal, inflation, months):
    st.subheader("Результат расчета")

    col1, col2 = st.columns(2)
    col1.metric("Собственные вложения", rubles(result["own_money"]))
    col2.metric("Процентный доход", rubles(result["interest"]))

    col3, col4 = st.columns(2)
    col3.metric("НДФЛ (оценка)", rubles(result["tax"]))
    col4.metric("Сумма после налога", rubles(result["after_tax"]))

    st.metric("Реальная стоимость в сегодняшних деньгах",
              rubles(result["real_value"]))

    future_goal = goal * ((1 + inflation / 100) ** (months / 12))
    st.write("Стоимость цели сегодня:", rubles(goal))
    st.write("Примерная стоимость цели к концу срока:", rubles(future_goal))

    if result["real_value"] >= goal:
        st.success("Финансовая цель достигнута.")
    else:
        st.warning("Финансовая цель пока не достигнута.")


# -------------------- ВЕБ-ИНТЕРФЕЙС --------------------

st.set_page_config(page_title="Калькулятор сбережений", page_icon="💰")

st.title("Калькулятор будущих сбережений")
st.write(
    "Программа помогает оценить, как будут расти накопления "
    "с учетом пополнений, процентов, налогов и инфляции."
)

st.info(
    "Это учебная модель, а не банковский или официальный налоговый калькулятор. "
    "Пополнение считается в конце каждого месяца."
)

mode = st.selectbox(
    "Выберите режим работы",
    [
        "1. Рассчитать будущие накопления",
        "2. Узнать срок достижения цели",
        "3. Рассчитать ежемесячное пополнение",
        "4. Рассчитать необходимую процентную ставку"
    ]
)

st.subheader("Общие данные")
initial_sum = st.number_input(
    "Первоначальная сумма, руб.", min_value=0.0,
    value=10000.0, step=1000.0
)

goal = st.number_input(
    "Финансовая цель (ее стоимость сегодня), руб.",
    min_value=1.0, value=100000.0, step=1000.0
)

inflation = st.number_input(
    "Предполагаемая инфляция за год, %",
    min_value=0.0, max_value=100.0, value=6.0, step=0.5
)

tax_free_limit = st.number_input(
    "Необлагаемый процентный доход за год, руб.",
    min_value=0.0, value=210000.0, step=10000.0
)
st.caption(
    "210 000 рублей указаны как пример лимита за 2025 год. "
    "Для другого налогового года значение нужно изменить."
)
st.caption(
    "В учебной модели введенный лимит повторяется для каждого расчетного "
    "периода из 12 месяцев. Это не точный расчет по календарным годам."
)

capitalization_name = st.selectbox(
    "Периодичность капитализации",
    ["Ежемесячная", "Ежеквартальная", "Ежегодная"]
)

if capitalization_name == "Ежемесячная":
    capitalization_months = 1
elif capitalization_name == "Ежеквартальная":
    capitalization_months = 3
else:
    capitalization_months = 12

st.subheader("Параметры выбранного режима")

if mode == "1. Рассчитать будущие накопления":
    monthly_payment = st.number_input(
        "Ежемесячное пополнение, руб.", min_value=0.0,
        value=3000.0, step=500.0
    )
    annual_rate = st.number_input(
        "Годовая процентная ставка, %", min_value=0.0,
        max_value=100.0, value=10.0, step=0.5
    )
    months = st.number_input(
        "Срок накопления, месяцев", min_value=1,
        max_value=600, value=36, step=1
    )

    if st.button("Рассчитать накопления"):
        result = calculate_savings(
            initial_sum, monthly_payment, int(months), annual_rate,
            inflation, tax_free_limit, capitalization_months
        )
        show_result(result, goal, inflation, int(months))

elif mode == "2. Узнать срок достижения цели":
    monthly_payment = st.number_input(
        "Ежемесячное пополнение, руб.", min_value=0.0,
        value=3000.0, step=500.0
    )
    annual_rate = st.number_input(
        "Годовая процентная ставка, %", min_value=0.0,
        max_value=100.0, value=10.0, step=0.5
    )

    if st.button("Найти срок"):
        months, result = find_months(
            initial_sum, monthly_payment, goal, annual_rate,
            inflation, tax_free_limit, capitalization_months
        )

        if months is None:
            st.warning("Цель не достигнута даже за 50 лет. Измените параметры.")
        else:
            st.success(
                "Для достижения цели потребуется примерно "
                + str(months) + " месяцев."
            )
            show_result(result, goal, inflation, months)

elif mode == "3. Рассчитать ежемесячное пополнение":
    annual_rate = st.number_input(
        "Годовая процентная ставка, %", min_value=0.0,
        max_value=100.0, value=10.0, step=0.5
    )
    months = st.number_input(
        "Срок накопления, месяцев", min_value=1,
        max_value=600, value=36, step=1
    )

    if st.button("Рассчитать пополнение"):
        payment = find_monthly_payment(
            initial_sum, goal, int(months), annual_rate,
            inflation, tax_free_limit, capitalization_months
        )

        if payment is None:
            st.warning("Не удалось подобрать сумму. Проверьте исходные данные.")
        else:
            st.success("Нужно откладывать примерно " + rubles(payment) + " в месяц.")
            result = calculate_savings(
                initial_sum, payment, int(months), annual_rate,
                inflation, tax_free_limit, capitalization_months
            )
            show_result(result, goal, inflation, int(months))

else:
    monthly_payment = st.number_input(
        "Ежемесячное пополнение, руб.", min_value=0.0,
        value=3000.0, step=500.0
    )
    months = st.number_input(
        "Срок накопления, месяцев", min_value=1,
        max_value=600, value=36, step=1
    )

    if st.button("Рассчитать ставку"):
        annual_rate = find_rate(
            initial_sum, monthly_payment, goal, int(months),
            inflation, tax_free_limit, capitalization_months
        )

        if annual_rate is None:
            st.warning(
                "Для достижения цели недостаточно даже ставки 100% годовых. "
                "Попробуйте увеличить срок или ежемесячное пополнение."
            )
        else:
            st.success(
                "Необходимая годовая ставка: "
                + str(round(annual_rate, 2)) + "%"
            )
            result = calculate_savings(
                initial_sum, monthly_payment, int(months), annual_rate,
                inflation, tax_free_limit, capitalization_months
            )
            show_result(result, goal, inflation, int(months))

st.divider()
st.caption(
    "Результаты являются приблизительными. Реальные условия вклада, "
    "налоговый расчет и инфляция могут отличаться от введенных значений."
)
