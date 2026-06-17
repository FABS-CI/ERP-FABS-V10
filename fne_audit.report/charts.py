import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Chart 1 — Conformité par axe
fig, ax = plt.subplots(figsize=(10, 6))
axes_labels = [
    "Infrastructure\nHTTPS/REST",
    "Auth\nBearer",
    "Gestion\nErreurs",
    "Payload\nVente",
    "Payload\nBordereau",
    "Payload\nAvoir",
    "QR Code\nDGI",
    "Settings\nConfig",
    "Frontend\nTests",
    "Spécimens\nPDF"
]
scores = [90, 80, 70, 55, 20, 60, 70, 30, 15, 0]
colors = ['#22c55e' if s >= 70 else '#f59e0b' if s >= 40 else '#ef4444' for s in scores]

bars = ax.barh(axes_labels, scores, color=colors, height=0.6, edgecolor='white')
ax.set_xlim(0, 100)
ax.set_xlabel('Conformité (%)', fontsize=11)
ax.set_title('Conformité DGI — Module FNE ERP-FABS-V10\npar axe d\'évaluation', fontsize=13, fontweight='bold', pad=15)
ax.axvline(x=70, color='#6b7280', linestyle='--', alpha=0.5, label='Seuil acceptable 70%')

for bar, score in zip(bars, scores):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
            f'{score}%', va='center', fontsize=9, fontweight='bold')

green = mpatches.Patch(color='#22c55e', label='Conforme (≥70%)')
orange = mpatches.Patch(color='#f59e0b', label='Partiel (40-69%)')
red = mpatches.Patch(color='#ef4444', label='Non conforme (<40%)')
ax.legend(handles=[green, orange, red], loc='lower right', fontsize=9)
ax.invert_yaxis()
plt.tight_layout()
fig.savefig('/home/user/ERP-FABS-V10/fne_audit.report/conformite_axes.png', dpi=150, bbox_inches='tight')
plt.close()

# Chart 2 — Scores globaux
fig2, ax2 = plt.subplots(figsize=(7, 5))
categories = ['Technique', 'Fonctionnel', 'DGI', 'Global']
scores2 = [72, 55, 48, 58]
colors2 = ['#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444']

bars2 = ax2.bar(categories, scores2, color=colors2, width=0.5, edgecolor='white', linewidth=1.5)
ax2.set_ylim(0, 100)
ax2.set_ylabel('Conformité (%)', fontsize=11)
ax2.set_title('Taux de conformité globaux\nModule FNE — ÉDITIONS FABS-CI', fontsize=13, fontweight='bold', pad=15)
ax2.axhline(y=70, color='#6b7280', linestyle='--', alpha=0.7, label='Seuil minimum 70%')
ax2.axhline(y=100, color='#22c55e', linestyle=':', alpha=0.4, label='Objectif 100%')

for bar, score in zip(bars2, scores2):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
             f'{score}%', ha='center', va='bottom', fontsize=12, fontweight='bold')

ax2.legend(fontsize=9)
plt.tight_layout()
fig2.savefig('/home/user/ERP-FABS-V10/fne_audit.report/conformite_globale.png', dpi=150, bbox_inches='tight')
plt.close()

print("Charts générés.")
