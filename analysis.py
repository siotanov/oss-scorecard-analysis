import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("viridis")
sns.set_context("notebook", font_scale=1.2)

%matplotlib inline

print("Done!")

RESULTS_DIR = Path("./results")

json_files = list(RESULTS_DIR.glob("*.json"))
print(f"Find JSON-files: {len(json_files)}")

if json_files:
    print("\nExammples find files:")
    for f in json_files[:5]:
        print(f"   - {f.name}")
else:
    print("\n File Not Found!")

def parse_scorecard_results(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    repo_name = data.get('repo', {}).get('name', 'unknown')
    date = data.get('date', 'unknown')
    aggregate_score = data.get('score', 0)

    checks = {}
    for check in data.get('checks', []):
        name = check.get('name', 'unknown')
        score = check.get('score', 0)
        checks[f'score_{name}'] = score

    reasons = {}
    for check in data.get('checks', []):
        name = check.get('name', 'unknown')
        reason = check.get('reason', '')
        reasons[f'reason_{name}'] = reason

    result = {
        'repository': repo_name,
        'date': date,
        'aggregate_score': aggregate_score,
        **checks,
        **reasons
    }

    return result

all_results = []
failed_files = []

for json_file in json_files:
    try:
        result = parse_scorecard_results(json_file)
        all_results.append(result)
    except Exception as e:
        failed_files.append((json_file.name, str(e)))
        print(f"Error {json_file.name}: {e}")

df = pd.DataFrame(all_results)

score_cols = [col for col in df.columns if col.startswith('score_')]
check_names = [col.replace('score_', '') for col in score_cols]

print("=" * 60)
print(f"Success load: {len(df)}")
print(f"Fail load: {len(failed_files)}")
print(f"Find: {len(score_cols)}")

if failed_files:
    print("\nError files:")
    for name, error in failed_files:
        print(f"   - {name}: {error[:50]}...")

if not df.empty:
    print("\nList checks:")
    for name in check_names[:10]:
        print(f"   - {name}")
    if len(check_names) > 10:
        print(f"   ... and {len(check_names) - 10} checks")

df.head()

if df.empty:
    print("Fail data analysis!")
else:
    print("=" * 60)
    print("Statistics:")
    print("=" * 60)

    print(f"\nAggregate Score:")
    print(f"   Quantity projects: {len(df)}")
    print(f"   middle:     {df['aggregate_score'].mean():.2f}")
    print(f"   median:     {df['aggregate_score'].median():.2f}")
    print(f"   min:     {df['aggregate_score'].min():.2f}")
    print(f"   max:    {df['aggregate_score'].max():.2f}")
    print(f"   st.dediation:   {df['aggregate_score'].std():.2f}")

    categories = {
        'Great (8-10)': len(df[df['aggregate_score'] >= 8]),
        'Good (6-8)': len(df[(df['aggregate_score'] >= 6) & (df['aggregate_score'] < 8)]),
        'Middle (4-6)': len(df[(df['aggregate_score'] >= 4) & (df['aggregate_score'] < 6)]),
        'Badly (2-4)': len(df[(df['aggregate_score'] >= 2) & (df['aggregate_score'] < 4)]),
        'Critical (<2)': len(df[df['aggregate_score'] < 2])
    }

    print(f"\nDdistribution by category]:")
    for cat, count in categories.items():
        pct = count / len(df) * 100
        bar = '█' * int(pct / 2)
        print(f"   {cat}: {count} ({pct:.1f}%) {bar}")

    check_means = {}
    for col in score_cols:
        check_name = col.replace('score_', '')
        check_means[check_name] = df[col].mean()

    top_checks = sorted(check_means.items(), key=lambda x: x[1], reverse=True)[:5]
    bottom_checks = sorted(check_means.items(), key=lambda x: x[1])[:5]


if not df.empty:
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    ax1 = axes[0]
    df['aggregate_score'].hist(bins=15, edgecolor='black', alpha=0.7,
                               color='steelblue', ax=ax1)
    ax1.axvline(df['aggregate_score'].mean(), color='red', linestyle='--',
                linewidth=2, label=f'Среднее: {df["aggregate_score"].mean():.2f}')
    ax1.axvline(df['aggregate_score'].median(), color='green', linestyle='--',
                linewidth=2, label=f'Медиана: {df["aggregate_score"].median():.2f}')
    ax1.set_title('Aggregate Score', fontsize=16)
    ax1.set_xlabel('Mark (0-10)')
    ax1.set_ylabel('Quantity projects')
    ax1.legend(fontsize=12)
    ax1.grid(True, alpha=0.3)

    ax2 = axes[1]
    df.boxplot(column='aggregate_score', ax=ax2)
    ax2.set_title('Aggregate Score (Boxplot)', fontsize=16)
    ax2.set_ylabel('Mark (0-10)')
    ax2.set_xticklabels(['Projects'])
    ax2.grid(True, alpha=0.3)

    plt.suptitle('Security analysis Open Source projects', fontsize=18, y=1.02)
    plt.tight_layout()
    plt.savefig('1_score_distribution.png', dpi=300, bbox_inches='tight')
    plt.show()
 if not df.empty:
    
    score_df = df[score_cols].copy()
    score_df.columns = check_names

    
    check_means = score_df.mean().sort_values(ascending=False)
    score_df = score_df[check_means.index]

    
    project_means = score_df.mean(axis=1)

    
    fig, ax = plt.subplots(figsize=(8.0, 11.0))

    sns.heatmap(
        score_df,
        cmap='RdYlGn',
        vmin=0,
        vmax=10,
        center=5,

        
        annot=False,

        linewidths=0.3,
        linecolor='white',

        cbar_kws={
            'label': 'Mark (0–10)',
            'shrink': 0.65
        },

        ax=ax
    )

    ax.set_title(
        'Heat map of ratings by inspections',
        fontsize=20,
        fontweight='bold',
        pad=20
    )

    ax.set_xlabel(
        'Checks',
        fontsize=13,
        labelpad=10
    )

    ax.set_ylabel(
        'Projetcs',
        fontsize=13,
        labelpad=10
    )

    ax.set_xticklabels(
        ax.get_xticklabels(),
        rotation=45,
        ha='right',
        fontsize=9
    )

    
    n_projects = len(score_df)

      if n_projects > 40:

        positions = list(range(0, n_projects, 5))

                if n_projects - 1 not in positions:
            positions.append(n_projects - 1)

        ax.set_yticks([p + 0.5 for p in positions])

        ax.set_yticklabels(
            [str(p + 1) for p in positions],
            fontsize=8,
            rotation=0
        )

    else:

        ax.set_yticklabels(
            [str(i + 1) for i in range(n_projects)],
            fontsize=8,
            rotation=0
        )

    cbar = ax.collections[0].colorbar

    cbar.set_label(
        'Mark (0–10)',
        fontsize=10
    )

    cbar.ax.tick_params(
        labelsize=9
    )

    plt.tight_layout()

    plt.savefig(
        '2_checks_heatmap.png',
        dpi=300,
        bbox_inches='tight',
        pad_inches=0.15
    )

    plt.show()

if not df.empty:
    check_means_sorted = check_means.sort_values()

    fig, ax = plt.subplots(figsize=(10, max(6, len(check_means_sorted) * 0.3)))

    
    colors = ['#2ecc71' if x >= 7 else '#f39c12' if x >= 5 else '#e74c3c'
              for x in check_means_sorted.values]
    bars = ax.barh(check_means_sorted.index, check_means_sorted.values, color=colors)

        ax.axvline(7, color='darkgreen', linestyle='--', alpha=0.7,
               label='Good (≥7)', linewidth=2)
    ax.axvline(5, color='orange', linestyle='--', alpha=0.7,
               label='Middle (5-7)', linewidth=2)
    ax.axvline(3, color='red', linestyle='--', alpha=0.7,
               label='Badly (<5)', linewidth=2)

    ax.set_xlabel('Avarege', fontsize=14)
    ax.set_title('Average scores for security checks', fontsize=16)
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)

    for i, bar in enumerate(bars):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                f'{bar.get_width():.2f}', va='center', fontsize=10)

    plt.tight_layout()
    plt.savefig('3_checks_average.png', dpi=300, bbox_inches='tight')
    plt.show()

if not df.empty:
    low_score_threshold = 5
    low_score_checks = {}
    for check in check_names:
        low_count = len(df[df[f'score_{check}'] < low_score_threshold])
        low_score_checks[check] = low_count / len(df) * 100

        sorted_low = sorted(low_score_checks.items(), key=lambda x: x[1], reverse=True)

    fig, ax = plt.subplots(figsize=(12, max(6, len(sorted_low) * 0.3)))
    checks, percentages = zip(*sorted_low[:15])  
    colors = ['#e74c3c' if p > 50 else '#f39c12' if p > 25 else '#2ecc71'
              for p in percentages[:15]]
    bars = ax.barh(checks, percentages[:15], color=colors)

        ax.axvline(50, color='red', linestyle='--', alpha=0.7, label='50% projects' linewidth=2)
    ax.axvline(25, color='orange', linestyle='--', alpha=0.7, label='25% projetcs', linewidth=2)

    ax.set_xlabel('%projects with scores < 5', fontsize=14)
    ax.set_title('The most problematic security checks', fontsize=16)
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)

        for i, bar in enumerate(bars):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f'{bar.get_width():.1f}%', va='center', fontsize=10)

    plt.tight_layout()
    plt.savefig('4_weak_points.png', dpi=300, bbox_inches='tight')
    plt.show()

if not df.empty:
    
    score_df = df[score_cols].copy()
    score_df.columns = check_names
    corr_matrix = score_df.corr()

        max_checks = 15
    if len(corr_matrix.columns) > max_checks:
      
        top_checks_names = check_means.nlargest(max_checks).index
        corr_matrix = corr_matrix.loc[top_checks_names, top_checks_names]

    fig, ax = plt.subplots(figsize=(12, 10))
    heatmap = sns.heatmap(corr_matrix,
                          annot=True,
                          fmt='.2f',
                          cmap='coolwarm',
                          center=0,
                          square=True,
                          cbar_kws={'label': 'Correlation coefficient', 'shrink': 0.8},
                          ax=ax,
                          vmin=-1, vmax=1)
    ax.set_title('Correlation between security checks', fontsize=16)
    plt.tight_layout()
    plt.savefig('5_correlation_matrix.png', dpi=300, bbox_inches='tight')
    plt.show()

    
