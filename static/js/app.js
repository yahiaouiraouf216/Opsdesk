// OpsDesk — JavaScript léger côté client.
// Ferme automatiquement les alertes flash après quelques secondes.

document.addEventListener("DOMContentLoaded", () => {
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach((alertEl) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
            bsAlert.close();
        }, 5000);
    });
});
