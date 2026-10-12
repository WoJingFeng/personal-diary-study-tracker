(function () {
    const canvas = document.getElementById("weeklyStudyChart");
    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    const labels = JSON.parse(canvas.dataset.labels || "[]");
    const values = JSON.parse(canvas.dataset.values || "[]");
    const isDark = document.documentElement.classList.contains("dark");

    const chart = new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "学习时长",
                    data: values,
                    backgroundColor: isDark ? "#78c6ad" : "#216b60",
                    borderWidth: 0,
                    borderRadius: 4,
                    maxBarThickness: 32
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.parsed.y || 0} 分钟`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: isDark ? "#a7b9ad" : "#66736d"
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: isDark ? "#35473c" : "#e7ece8"
                    },
                    ticks: {
                        precision: 0,
                        color: isDark ? "#a7b9ad" : "#66736d"
                    }
                }
            }
        }
    });

    document.querySelector("[data-theme-toggle]")?.addEventListener("click", () => {
        const dark = document.documentElement.classList.contains("dark");
        chart.data.datasets[0].backgroundColor = dark ? "#78c6ad" : "#216b60";
        chart.options.scales.x.ticks.color = dark ? "#a7b9ad" : "#66736d";
        chart.options.scales.y.ticks.color = dark ? "#a7b9ad" : "#66736d";
        chart.options.scales.y.grid.color = dark ? "#35473c" : "#e7ece8";
        chart.update();
    });
})();
