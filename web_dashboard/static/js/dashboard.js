/**
 * Real-Time IoT Monitoring and Analytics Dashboard Controller
 * Academic M.E. Project: Automated Carrot Quality Detection and Sorting System
 */

document.addEventListener("DOMContentLoaded", () => {
    // Chart instances
    let distributionChart = null;
    let throughputChart = null;

    // Initialize Chart.js
    initCharts();

    // Attach Event Listeners
    setupEventListeners();

    // Initial Data Fetch
    fetchTelemetry();
    fetchStatistics();
    fetchDetections();

    // Start Real-Time Polling (Every 1500ms)
    setInterval(() => {
        fetchTelemetry();
        fetchStatistics();
        fetchDetections();
    }, 1500);

    // -------------------------------------------------------------------------
    // Chart Initializations
    // -------------------------------------------------------------------------
    function initCharts() {
        const distCtx = document.getElementById("distributionChart");
        if (distCtx) {
            distributionChart = new Chart(distCtx, {
                type: "doughnut",
                data: {
                    labels: ["Good Carrots", "Damaged Carrots", "Rotten Carrots"],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: ["#10b981", "#f59e0b", "#ef4444"],
                        borderColor: "#1e293b",
                        borderWidth: 2,
                        hoverOffset: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: { color: "#94a3b8", font: { size: 12 } }
                        }
                    },
                    cutout: "70%"
                }
            });
        }

        const thruCtx = document.getElementById("throughputChart");
        if (thruCtx) {
            throughputChart = new Chart(thruCtx, {
                type: "line",
                data: {
                    labels: [],
                    datasets: [{
                        label: "Inspections / Hour",
                        data: [],
                        borderColor: "#06b6d4",
                        backgroundColor: "rgba(6, 182, 212, 0.15)",
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: "#06b6d4"
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            grid: { color: "rgba(255, 255, 255, 0.05)" },
                            ticks: { color: "#94a3b8" }
                        },
                        y: {
                            beginAtZero: true,
                            grid: { color: "rgba(255, 255, 255, 0.05)" },
                            ticks: { color: "#94a3b8", stepSize: 5 }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    }

    // -------------------------------------------------------------------------
    // API Polling Functions
    // -------------------------------------------------------------------------
    async function fetchTelemetry() {
        try {
            const res = await fetch("/api/status");
            const json = await res.json();
            if (!json.success) return;

            const d = json.data;
            // System status dot and text
            const statusDot = document.getElementById("systemStatusDot");
            const statusText = document.getElementById("systemStatusText");
            if (statusDot && statusText) {
                if (d.is_system_active) {
                    statusDot.className = "status-dot active";
                    statusText.textContent = "SYSTEM ACTIVE";
                } else {
                    statusDot.className = "status-dot inactive";
                    statusText.textContent = "SYSTEM PAUSED";
                }
            }

            // Camera status
            const camBadge = document.getElementById("cameraBadge");
            if (camBadge) {
                camBadge.textContent = d.camera.is_simulation ? "CAM: SIMULATION" : "CAM: HARDWARE USB";
                camBadge.className = d.camera.is_simulation ? "video-badge text-warning" : "video-badge text-success";
            }

            // Conveyor status
            const convSpeedEl = document.getElementById("telemetryConvSpeed");
            if (convSpeedEl) {
                convSpeedEl.textContent = d.conveyor.is_running 
                    ? `${d.conveyor.speed_percent}% (${d.conveyor.velocity_mps} m/s)`
                    : "STOPPED";
            }

            // Servo Actuator status
            const servoPosEl = document.getElementById("telemetryServoPos");
            if (servoPosEl) {
                servoPosEl.textContent = `${d.sorter.current_bin} [${d.sorter.current_angle}°]`;
            }

            // IR Sensor state
            const irStateEl = document.getElementById("telemetryIrState");
            if (irStateEl) {
                irStateEl.textContent = d.ir_sensor.is_object_present ? "TRIGGERED (CARROT DETECTED)" : "BEAM CLEAR";
                irStateEl.className = d.ir_sensor.is_object_present ? "fw-bold text-warning" : "text-secondary";
            }

        } catch (err) {
            console.error("Telemetry fetch error:", err);
        }
    }

    async function fetchStatistics() {
        try {
            const res = await fetch("/api/stats");
            const json = await res.json();
            if (!json.success) return;

            const s = json.data;
            // Update KPI cards
            updateElement("kpiTotal", s.total_inspected);
            updateElement("kpiGood", s.good_count);
            updateElement("kpiGoodPct", `${s.good_percent}%`);
            updateElement("kpiDamaged", s.damaged_count);
            updateElement("kpiDamagedPct", `${s.damaged_percent}%`);
            updateElement("kpiRotten", s.rotten_count);
            updateElement("kpiRottenPct", `${s.rotten_percent}%`);
            updateElement("kpiEfficiency", `${s.sorting_efficiency}%`);

            // Update Doughnut Chart
            if (distributionChart) {
                distributionChart.data.datasets[0].data = [s.good_count, s.damaged_count, s.rotten_count];
                distributionChart.update();
            }

            // Update Throughput Chart
            if (throughputChart && s.timeline && s.timeline.length > 0) {
                throughputChart.data.labels = s.timeline.map(t => t.hour);
                throughputChart.data.datasets[0].data = s.timeline.map(t => t.hourly_total);
                throughputChart.update();
            }

        } catch (err) {
            console.error("Statistics fetch error:", err);
        }
    }

    async function fetchDetections() {
        try {
            const res = await fetch("/api/detections?limit=10");
            const json = await res.json();
            if (!json.success || !json.data) return;

            const records = json.data;
            const tbody = document.getElementById("detectionsTableBody");
            if (!tbody) return;

            if (records.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4">No inspection events recorded yet. Click 'Simulate IR Trigger' to inspect.</td></tr>`;
                return;
            }

            // Update Latest Card with record[0]
            const latest = records[0];
            updateElement("latestClass", latest.class_name);
            updateElement("latestConfidence", `${(latest.confidence * 100).toFixed(1)}%`);
            updateElement("latestBin", latest.target_bin);
            updateElement("latestTimestamp", latest.timestamp);

            const confBar = document.getElementById("latestConfBar");
            if (confBar) {
                const pct = (latest.confidence * 100).toFixed(1);
                confBar.style.width = `${pct}%`;
                confBar.className = `progress-bar ${latest.class_id === 0 ? "bg-success" : (latest.class_id === 1 ? "bg-warning" : "bg-danger")}`;
            }

            const previewImg = document.getElementById("latestPreviewImg");
            if (previewImg && latest.image_path) {
                previewImg.src = latest.image_path;
            }

            // Populate table rows
            tbody.innerHTML = records.map(r => {
                let badgeClass = "badge-reject";
                if (r.class_id === 0) badgeClass = "badge-good";
                else if (r.class_id === 1) badgeClass = "badge-damaged";
                else if (r.class_id === 2) badgeClass = "badge-rotten";

                return `
                    <tr>
                        <td class="fw-bold">#${r.id}</td>
                        <td class="text-secondary">${r.timestamp}</td>
                        <td><span class="badge ${badgeClass} px-2 py-1">${r.class_name}</span></td>
                        <td>${(r.confidence * 100).toFixed(1)}%</td>
                        <td><span class="badge bg-dark border text-light px-2 py-1">${r.target_bin}</span></td>
                        <td><span class="badge bg-secondary">${r.sorting_status}</span></td>
                    </tr>
                `;
            }).join("");

        } catch (err) {
            console.error("Detections fetch error:", err);
        }
    }

    // -------------------------------------------------------------------------
    // Event Listeners and Button Handlers
    // -------------------------------------------------------------------------
    function setupEventListeners() {
        // Manual IR trigger button
        const triggerBtn = document.getElementById("btnTriggerInspection");
        if (triggerBtn) {
            triggerBtn.addEventListener("click", async () => {
                triggerBtn.disabled = true;
                triggerBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Inspecting...`;
                try {
                    const res = await fetch("/api/trigger", { method: "POST" });
                    const json = await res.json();
                    if (json.success) {
                        fetchDetections();
                        fetchStatistics();
                    } else {
                        alert(`Inspection error: ${json.message}`);
                    }
                } catch (e) {
                    console.error(e);
                } finally {
                    triggerBtn.disabled = false;
                    triggerBtn.innerHTML = `<i class="bi bi-camera me-1"></i> Simulate IR Trigger`;
                }
            });
        }

        // System Start/Stop
        const startSysBtn = document.getElementById("btnStartSystem");
        if (startSysBtn) {
            startSysBtn.addEventListener("click", () => sendSystemAction("/api/system/start"));
        }

        const stopSysBtn = document.getElementById("btnStopSystem");
        if (stopSysBtn) {
            stopSysBtn.addEventListener("click", () => sendSystemAction("/api/system/stop"));
        }

        // Conveyor controls
        const convStartBtn = document.getElementById("btnConveyorStart");
        if (convStartBtn) {
            convStartBtn.addEventListener("click", () => sendConveyorAction("start"));
        }

        const convStopBtn = document.getElementById("btnConveyorStop");
        if (convStopBtn) {
            convStopBtn.addEventListener("click", () => sendConveyorAction("stop"));
        }

        const convSpeedRange = document.getElementById("conveyorSpeedRange");
        if (convSpeedRange) {
            convSpeedRange.addEventListener("change", (e) => {
                sendConveyorAction("set_speed", e.target.value);
            });
        }

        // Servo test buttons
        document.querySelectorAll("[data-servo-bin]").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const binNum = parseInt(e.currentTarget.getAttribute("data-servo-bin"));
                sendServoTest(binNum);
            });
        });

        // Clear history button
        const clearBtn = document.getElementById("btnClearHistory");
        if (clearBtn) {
            clearBtn.addEventListener("click", async () => {
                if (confirm("Reset all inspection records and statistics?")) {
                    await fetch("/api/history/clear", { method: "POST" });
                    fetchStatistics();
                    fetchDetections();
                }
            });
        }
    }

    async function sendSystemAction(endpoint) {
        try {
            await fetch(endpoint, { method: "POST" });
            fetchTelemetry();
        } catch (e) {
            console.error(e);
        }
    }

    async function sendConveyorAction(action, speed = null) {
        try {
            await fetch("/api/conveyor/control", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action, speed })
            });
            fetchTelemetry();
        } catch (e) {
            console.error(e);
        }
    }

    async function sendServoTest(binNum) {
        try {
            await fetch("/api/servo/test", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ bin: binNum })
            });
            fetchTelemetry();
        } catch (e) {
            console.error(e);
        }
    }

    function updateElement(id, value) {
        const el = document.getElementById(id);
        if (el && value !== undefined && value !== null) {
            el.textContent = value;
        }
    }
});
