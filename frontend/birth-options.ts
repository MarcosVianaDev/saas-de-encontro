export const birthMonths = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

export const latestBirthYear = new Date().getFullYear() - 18;
export const birthYears = Array.from(
  { length: latestBirthYear - 1900 + 1 },
  (_, index) => latestBirthYear - index,
);
