(function () {
  const dataElement = document.getElementById('dashboard-chart-data');

  if (!dataElement || !window.Chart) {
    return;
  }

  const chartData = JSON.parse(dataElement.textContent);
  const palette = ['#38bdf8', '#3ddc97', '#f8c14a', '#fb7185', '#a78bfa', '#60a5fa', '#f472b6', '#34d399'];
  const isLightTheme = document.body.classList.contains('theme-claro');
  const chartTextColor = isLightTheme ? '#33445a' : '#aebdd0';
  const chartGridColor = isLightTheme ? 'rgba(15, 39, 66, 0.1)' : 'rgba(148, 163, 184, 0.12)';
  const chartBorderColor = isLightTheme ? '#ffffff' : '#111925';

  Chart.defaults.color = chartTextColor;
  Chart.defaults.font.family = 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
  Chart.defaults.borderColor = chartGridColor;

  function splitData(items) {
    return {
      labels: items.map((item) => item.label),
      values: items.map((item) => item.value),
      ids: items.map((item) => item.ids || []),
    };
  }

  function formatIds(ids) {
    if (!ids.length) {
      return ['IDs: -'];
    }

    const lines = ['IDs:'];

    for (let index = 0; index < ids.length; index += 6) {
      lines.push(ids.slice(index, index + 6).join(', '));
    }

    return lines;
  }

  function chartOptions(extra = {}) {
    const extraPlugins = extra.plugins || {};

    return {
      responsive: true,
      maintainAspectRatio: false,
      ...extra,
      plugins: {
        legend: {
          labels: {
            boxWidth: 12,
            boxHeight: 12,
            usePointStyle: true,
          },
        },
        tooltip: {
          callbacks: {
            label(context) {
              return `Quantidade: ${context.formattedValue}`;
            },
            afterLabel(context) {
              const ids = context.dataset.ids?.[context.dataIndex] || [];

              return formatIds(ids);
            },
          },
        },
        ...extraPlugins,
      },
    };
  }

  function renderDoughnut(id, items) {
    const canvas = document.getElementById(id);

    if (!canvas) {
      return;
    }

    const current = splitData(items);

    new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: current.labels,
        datasets: [{
          data: current.values,
          ids: current.ids,
          backgroundColor: palette,
          borderColor: chartBorderColor,
          borderWidth: 3,
          hoverOffset: 6,
        }],
      },
      options: chartOptions({
        cutout: '68%',
      }),
    });
  }

  function renderBar(id, items, horizontal) {
    const canvas = document.getElementById(id);

    if (!canvas) {
      return;
    }

    const current = splitData(items);

    new Chart(canvas, {
      type: 'bar',
      data: {
        labels: current.labels,
        datasets: [{
          data: current.values,
          ids: current.ids,
          backgroundColor: palette.map((color) => `${color}cc`),
          borderColor: palette,
          borderWidth: 1,
          borderRadius: 6,
          maxBarThickness: 44,
        }],
      },
      options: chartOptions({
        indexAxis: horizontal ? 'y' : 'x',
        scales: {
          x: {
            beginAtZero: true,
            ticks: {
              precision: 0,
            },
            grid: {
              color: chartGridColor,
            },
          },
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0,
            },
            grid: {
              color: isLightTheme ? 'rgba(15, 39, 66, 0.07)' : 'rgba(148, 163, 184, 0.08)',
            },
          },
        },
        plugins: {
          legend: {
            display: false,
          },
        },
      }),
    });
  }

  renderDoughnut('statusChart', chartData.status || []);
  renderBar('salasChart', chartData.salas || [], true);
  renderDoughnut('windowsChart', chartData.windows || []);
  renderBar('ramChart', chartData.ram || [], false);
}());
