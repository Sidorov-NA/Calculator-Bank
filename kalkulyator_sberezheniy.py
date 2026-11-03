import streamlit as st


def calculate_tax(year_interest, tax_free_limit):
    tax_base = year_interest - tax_free_limit

    if tax_base < 0:
        tax_base = 0

    if tax_base <= 2400000:
        tax = tax_base * 0.13
    else:
        tax = 2400000 * 0.13 + (tax_base - 2400000) * 0.15

    return tax


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
        interest = balance * monthly_rate

        pending_interest += interest
        total_interest += interest
        year_interest += interest

        if month % capitalization_months == 0:
            balance += pending_interest
            pending_interest = 0

        balance += monthly_payment
        own_money += monthly_payment

        if month % 12 == 0:
            total_tax += calculate_tax(year_interest, tax_free_limit)
            year_interest = 0

    if year_interest > 0:
        total_tax += calculate_tax(year_interest, tax_free_limit)

    balance += pending_interest

    after_tax = balance - total_tax

    if after_tax < 0:
        after_tax = 0

    years = months / 12
    real_value = after_tax / ((1 + inflation / 100) ** years)

    return {
        "own_money": own_money,
        "interest": total_interest,
        "tax": total_tax,
        "after_tax": after_tax,
        "real_value": real_value
    }


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


def find_payment(initial_sum, goal, months,
                 annual_rate, inflation, tax_free_limit,
                 capitalization_months):

    low = 0
    high = 1000

    while high < 1000000000000:
        result = calculate_savings(
            initial_sum, high, months, annual_rate,
            inflation, tax_free_limit, capitalization_months
        )

        if result["real_value"] >= goal:
            break

        high *= 2

    if high >= 1000000000000:
        return None

    for i in range(40):
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

    for i in range(40):
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


def rubles(value):
    return str(round(value, 2)) + " руб."


def show_result(result):
    st.subheader("Результат")

    st.write("Вложено собственных денег:", rubles(result["own_money"]))
    st.write("Получено процентов:", rubles(result["interest"]))
    st.write("Примерный налог:", rubles(result["tax"]))
    st.write("Сумма после налога:", rubles(result["after_tax"]))
    st.write("С учетом инфляции:", rubles(result["real_value"]))

st.title("Калькулятор сбережений")

mode = st.selectbox(
    "Выберите режим",
    [
        "Рассчитать накопления",
        "Узнать срок накопления",
        "Рассчитать ежемесячный взнос",
        "Рассчитать процентную ставку"
    ]
)

st.subheader("Общие данные")

initial_sum = st.number_input(
    "Начальная сумма, руб.", min_value=0.0, value=10000.0
)

goal = st.number_input(
    "Финансовая цель, руб.", min_value=1.0, value=100000.0
)

inflation = st.number_input(
    "Инфляция, %", min_value=0.0, value=6.0
)

tax_free_limit = st.number_input(
    "Необлагаемый доход, руб.", min_value=0.0, value=210000.0
)

capitalization = st.selectbox(
    "Капитализация",
    ["Ежемесячная", "Ежеквартальная", "Ежегодная"]
)

if capitalization == "Ежемесячная":
    capitalization_months = 1
elif capitalization == "Ежеквартальная":
    capitalization_months = 3
else:
    capitalization_months = 12


st.subheader("Расчет")

if mode == "Рассчитать накопления":

    monthly_payment = st.number_input(
        "Ежемесячный взнос, руб.", min_value=0.0, value=3000.0
    )

    annual_rate = st.number_input(
        "Процентная ставка, %", min_value=0.0, value=10.0
    )

    months = st.number_input(
        "Срок в месяцах", min_value=1, max_value=600, value=36
    )

    if st.button("Рассчитать"):
        result = calculate_savings(
            initial_sum, monthly_payment, int(months),
            annual_rate, inflation, tax_free_limit,
            capitalization_months
        )

        show_result(result)

elif mode == "Узнать срок накопления":

    monthly_payment = st.number_input(
        "Ежемесячный взнос, руб.", min_value=0.0, value=3000.0
    )

    annual_rate = st.number_input(
        "Процентная ставка, %", min_value=0.0, value=10.0
    )

    if st.button("Рассчитать"):
        months, result = find_months(
            initial_sum, monthly_payment, goal, annual_rate,
            inflation, tax_free_limit, capitalization_months
        )

        if months is None:
            st.write("Цель не достигнута за 50 лет.")
        else:
            st.write("Необходимый срок:", months, "месяцев")
            show_result(result)

elif mode == "Рассчитать ежемесячный взнос":

    annual_rate = st.number_input(
        "Процентная ставка, %", min_value=0.0, value=10.0
    )

    months = st.number_input(
        "Срок в месяцах", min_value=1, max_value=600, value=36
    )

    if st.button("Рассчитать"):
        payment = find_payment(
            initial_sum, goal, int(months), annual_rate,
            inflation, tax_free_limit, capitalization_months
        )

        if payment is None:
            st.write("Не удалось подобрать сумму.")
        else:
            st.write("Необходимый взнос:", rubles(payment))

elif mode == "Рассчитать процентную ставку":

    monthly_payment = st.number_input(
        "Ежемесячный взнос, руб.", min_value=0.0, value=3000.0
    )

    months = st.number_input(
        "Срок в месяцах", min_value=1, max_value=600, value=36
    )

    if st.button("Рассчитать"):
        annual_rate = find_rate(
            initial_sum, monthly_payment, goal, int(months),
            inflation, tax_free_limit, capitalization_months
        )

        if annual_rate is None:
            st.write("Необходимую ставку подобрать не удалось.")
        else:
            st.write("Необходимая ставка:", round(annual_rate, 2), "%")