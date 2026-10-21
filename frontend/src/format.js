const wholeFormat = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  maximumFractionDigits: 0,
})

const kopecksFormat = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

// 1200 -> «1 200 ₽», 33.5 -> «33,50 ₽»
export function formatMoney(value) {
  const number = Number(value)
  if (Number.isInteger(number)) {
    return wholeFormat.format(number)
  }
  return kopecksFormat.format(number)
}
