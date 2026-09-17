(function () {
    const canvas = document.getElementById("weeklyStudyChart");
    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    const labels = JSON.parse(canvas.dataset.labels || "[]");
    const values = JSON.parse(canvas.dataset.values || "[]");
    const isDark = document.documentElement.classList.contains("dark");

    new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "学习时长",
                    data: values,
                    backgroundColor: isDark ? "rgba(52, 211, 153, 0.75)" : "rgba(47, 111, 94, 0.82)",
                    borderColor: isDark ? "rgb(52, 211, 153)" : "rgb(47, 111, 94)",
                    borderWidth: 1,
                    borderRadius: 6,
                    maxBarThickness: 42
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
                        color: isDark ? "#cbd5e1" : "#475569"
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: isDark ? "rgba(51, 65, 85, 0.7)" : "rgba(203, 213, 225, 0.8)"
                    },
                    ticks: {
                        precision: 0,
                        color: isDark ? "#cbd5e1" : "#475569"
                    }
                }
            }
        }
    });
})();
