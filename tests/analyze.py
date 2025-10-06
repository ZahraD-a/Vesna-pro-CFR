import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

Qs = { "it": ["riservata", "che generalmente accorda fiducia", "dedita al lavoro", "rilassata, che tiene bene lo stress sotto controllo", "con una immaginazione vivace", "estroversa, socievole", "che tende a rilevare difetti altrui", "tendente alla pigrizia", "che si innervosisce facilmente", "che ha scarsi interessi artistici "], "en": ["is reserved", "is generally trusting", "does a thorough job", "is relaxed, handles stress well", "has an active imagination", "is outgoing, sociable", "tends to find fault with others", "tends to be lazy", "gets nervous easily", "has few artistic interests"]}
CHECK_FIELD = {"it": "riservata", "en": "is reserved"}
SUFFIXES = [1, 3, 5, 7]
SCORES = {"it": {"totalmente d'accordo": 1, "d'accordo": 0.5, "né d'accordo, né in disaccordo": 0, "in disaccordo": -0.5, "totalmente in disaccordo": -1},
        "en": {"agree strongly": 1, "agree": 0.5, "neither agree nor disagree": 0, "disagree": -0.5, "disagree strongly": -1} }

class Entry():

    def __init__(self, test, name, lang, questions):
        self.test = test
        self.name = name
        self.answers = []
        self.lang = lang
        for q in questions:
            if not isinstance( q, str ):
                self.answers.append( None )
                continue
            q = q.strip().lower()
            if q in SCORES[lang].keys():
                self.answers.append( SCORES[lang][q])
            else:
                self.answers.append( None )

    def get_ans( self, i : int ):
        return self.answers[ i ]

    def __str__(self):
        return "Test n " + str(self.test) + ", name: " + self.name + " ans: " + str( self.answers )

class Partecipant():

    def __init__(self, name: str, o: int, c: int, e: int, a: int, n: int ):
        self.name = name
        self.o = o
        self.c = c
        self.e = e
        self.a = a
        self.n = n
    
    def __str__( self ):
        return self.name.title() + "\n Openness:\t" + str( self.o ) + "\n Carefulness:\t" + str(self.c) + "\n Extraversion\t" + str( self.e) + "\n Amicability: " + str( self.a ) + "\n Neuroticism: " + str( self.n)

    def to_df(self):
        return pd.DataFrame(
            {
            "r": [self.o, self.c, self.e, self.a, self.n],
            "theta": ["Openness", "Carefulness", "Extraversion", "Amicability", "Neuroticism"]
            }
        )


class Test:
    
    def __init__(self, number: int):
        self.number = number

    def __str__(self):
        s = f"\n{'='*60}\n"
        s += f"TEST {self.number:2d}"
        s += f"\n{'='*60}\n"
        
        if "alice" in dir(self) and "bob" in dir(self):
            s += "\nMODEL PERSONALITIES:\n"
            s += "-" * 40 + "\n"
            s += f"{'Trait':<15} {'Alice':<10} {'Bob':<10}\n"
            s += "-" * 40 + "\n"
            s += f"{'Openness':<15} {self.alice.o:<10.3f} {self.bob.o:<10.3f}\n"
            s += f"{'Carefulness':<15} {self.alice.c:<10.3f} {self.bob.c:<10.3f}\n"
            s += f"{'Extraversion':<15} {self.alice.e:<10.3f} {self.bob.e:<10.3f}\n"
            s += f"{'Amicability':<15} {self.alice.a:<10.3f} {self.bob.a:<10.3f}\n"
            s += f"{'Neuroticism':<15} {self.alice.n:<10.3f} {self.bob.n:<10.3f}\n"
            
        if "entries" in dir( self ):
            s += f"\nDATA ENTRIES: {len(self.entries)} total responses\n"
            alice_count = sum(1 for e in self.entries if e.name == "alice")
            bob_count = sum(1 for e in self.entries if e.name == "bob")
            s += f"  - Alice: {alice_count} responses\n"
            s += f"  - Bob:   {bob_count} responses\n"
        return s

    def add_partecipant( self, p : Partecipant ):
        if p.name == "alice":
            self.alice = p
        else:
            self.bob = p
    
    def add_entry( self, e : Entry ):
        if "entries" not in dir(self):
            self.entries = [ ]
        self.entries.append( e )

    def export_to_markdown(self, stats_mean, stats_var, counts):
        """Export analysis results to a Markdown file"""
        filename = f"analysis-test-{self.number}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# Personality Perception Analysis - Test {self.number}\n\n")
            
            # Model personalities table
            f.write("## Model Personalities\n\n")
            f.write("| Trait | Alice | Bob |\n")
            f.write("|-------|-------|-----|\n")
            f.write(f"| Openness | {self.alice.o:.3f} | {self.bob.o:.3f} |\n")
            f.write(f"| Carefulness | {self.alice.c:.3f} | {self.bob.c:.3f} |\n")
            f.write(f"| Extraversion | {self.alice.e:.3f} | {self.bob.e:.3f} |\n")
            f.write(f"| Amicability | {self.alice.a:.3f} | {self.bob.a:.3f} |\n")
            f.write(f"| Neuroticism | {self.alice.n:.3f} | {self.bob.n:.3f} |\n\n")
            
            # Data summary
            if "entries" in dir(self):
                alice_count = sum(1 for e in self.entries if e.name == "alice")
                bob_count = sum(1 for e in self.entries if e.name == "bob")
                f.write("## Data Summary\n\n")
                f.write(f"- **Total responses**: {len(self.entries)}\n")
                f.write(f"- **Alice responses**: {alice_count}\n")
                f.write(f"- **Bob responses**: {bob_count}\n\n")
            
            # Results analysis
            f.write("## Results Analysis\n\n")
            
            trait_names = ["Openness", "Carefulness", "Extraversion", "Amicability", "Neuroticism"]
            
            for name in stats_mean:
                if counts[name] == 0:
                    continue
                    
                f.write(f"### {name.title()} (n={counts[name]} responses)\n\n")
                
                # Results table
                f.write("| Trait | Model | Perceived | Variance | Distance | Accuracy |\n")
                f.write("|-------|-------|-----------|----------|----------|-----------|\n")
                
                mean = stats_mean[name]
                var = stats_var[name]
                model_values = [getattr(self, name).o, getattr(self, name).c, 
                              getattr(self, name).e, getattr(self, name).a, getattr(self, name).n]
                
                total_distance = 0
                for i, trait in enumerate(trait_names):
                    distance = abs(mean[i] - model_values[i])
                    total_distance += distance
                    accuracy = max(0, (1 - distance) * 100)
                    
                    f.write(f"| {trait} | {model_values[i]:.3f} | {mean[i]:.3f} | {var[i]:.3f} | {distance:.3f} | {accuracy:.1f}% |\n")
                
                # Average row
                avg_distance = total_distance / 5
                avg_accuracy = max(0, (1 - avg_distance) * 100)
                f.write(f"| **AVERAGE** | - | - | - | **{avg_distance:.3f}** | **{avg_accuracy:.1f}%** |\n\n")
                
                # Summary insights
                distances = [abs(mean[i] - model_values[i]) for i in range(5)]
                best_perceived = trait_names[distances.index(min(distances))]
                worst_perceived = trait_names[distances.index(max(distances))]
                
                f.write(f"**Key Insights:**\n")
                f.write(f"- Most accurately perceived trait: **{best_perceived}** (distance: {min(distances):.3f})\n")
                f.write(f"- Least accurately perceived trait: **{worst_perceived}** (distance: {max(distances):.3f})\n")
                f.write(f"- Overall perception accuracy: **{avg_accuracy:.1f}%**\n\n")
            
            # Chart reference
            f.write("## Visualization\n\n")
            f.write(f"The main comparison chart has been saved as:\n")
            f.write(f"- Static: `result-test-{self.number}.png`\n")
            f.write(f"- Interactive: `result-test-{self.number}.html`\n\n")
            f.write(f"The distribution analysis chart has been saved as:\n")
            f.write(f"- Static: `distributions-test-{self.number}.png`\n")
            f.write(f"- Interactive: `distributions-test-{self.number}.html`\n\n")
            f.write(f"The OCEAN spider/radar chart has been saved as:\n")
            f.write(f"- Static: `spider-test-{self.number}.png`\n")
            f.write(f"- Interactive: `spider-test-{self.number}.html`\n\n")
            
            # Timestamp
            from datetime import datetime
            f.write("---\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        print(f"Analisi esportata in Markdown: {filename}")
        return filename

    def create_distribution_plots(self, stats_mean, stats_var, counts):
        """Create histogram plots for each trait showing individual scores and model values"""
        traits = ["Openness", "Carefulness", "Extraversion", "Amicability", "Neuroticism"]
        
        # Collect all individual scores per participant and trait
        individual_scores = {"alice": [[] for _ in range(5)], "bob": [[] for _ in range(5)]}
        
        for entry in self.entries:
            name = entry.name
            # Compute per-entry trait vector
            vec = [0.0] * 5  # [O, C, E, A, N]
            valid = False
            
            # Map answers to traits (same logic as in compute_stats)
            ans = [entry.get_ans(i) for i in range(10)]
            if ans[0] is not None:
                vec[2] += ans[0] * -1; valid = True  # Extraversion
            if ans[1] is not None:
                vec[3] += ans[1]; valid = True       # Amicability
            if ans[2] is not None:
                vec[1] += ans[2] * -1; valid = True  # Carefulness
            if ans[3] is not None:
                vec[4] += ans[3] * -1; valid = True  # Neuroticism
            if ans[4] is not None:
                vec[0] += ans[4] * -1; valid = True  # Openness
            if ans[5] is not None:
                vec[2] += ans[5]; valid = True       # Extraversion
            if ans[6] is not None:
                vec[3] += ans[6] * -1; valid = True  # Amicability
            if ans[7] is not None:
                vec[1] += ans[7]; valid = True       # Carefulness
            if ans[8] is not None:
                vec[4] += ans[8]; valid = True       # Neuroticism
            if ans[9] is not None:
                vec[0] += ans[9]; valid = True       # Openness
            
            if valid:
                for i in range(5):
                    individual_scores[name][i].append(vec[i] / 2)  # Normalize to [-1, +1]
        
        # Create subplot grid: 2 rows (Alice, Bob) × 5 cols (traits)
        fig = make_subplots(
            rows=2, cols=5,
            subplot_titles=[f"Alice - {trait}" for trait in traits] + [f"Bob - {trait}" for trait in traits],
            vertical_spacing=0.1,  # Increased spacing between Alice and Bob rows
            horizontal_spacing=0.05
        )
        
        colors = {'alice': '#ff7f0e', 'bob': '#1f77b4'}  # Orange for Alice, Blue for Bob
        
        for participant_idx, name in enumerate(['alice', 'bob']):
            if counts[name] == 0:
                continue
                
            model_values = [getattr(self, name).o, getattr(self, name).c, 
                          getattr(self, name).e, getattr(self, name).a, getattr(self, name).n]
            
            for trait_idx in range(5):
                scores = individual_scores[name][trait_idx]
                if len(scores) == 0:
                    continue
                
                # Calculate statistics
                mean_score = np.mean(scores)
                std_score = np.std(scores, ddof=1) if len(scores) > 1 else 0
                
                row = participant_idx + 1
                col = trait_idx + 1
                print(scores)
                
                # Create histogram
                fig.add_trace(
                    go.Histogram(
                        x=scores,
                        nbinsx=20,  # Number of bins
                        name=f'{name.title()} - {traits[trait_idx]}',
                        marker_color=colors[name],
                        opacity=0.7,
                        showlegend=False
                    ),
                    row=row, col=col
                )
                
                # Add vertical line for model (true) value
                fig.add_vline(
                    x=model_values[trait_idx],
                    line=dict(color='red', width=3, dash='dash'),
                    row=row, col=col
                )
                
                # Get the max count for positioning annotations
                hist_counts, bin_edges = np.histogram(scores, bins=20, range=(-1, 1))
                max_count = max(hist_counts) if len(hist_counts) > 0 else 1
                
                # Add text annotation for model value
                fig.add_annotation(
                    x=model_values[trait_idx],
                    y=max_count * 0.9,
                    text=f"True: {model_values[trait_idx]:.2f}",
                    showarrow=False,
                    font=dict(color='red', size=10),
                    row=row, col=col
                )
                
                # Add text annotation for statistics
                fig.add_annotation(
                    x=-0.95,
                    y=max_count * 0.7,
                    text=f"μ: {mean_score:.2f}<br>σ: {std_score:.2f}<br>n: {len(scores)}",
                    showarrow=False,
                    font=dict(size=9),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="gray",
                    borderwidth=1,
                    row=row, col=col
                )
        
        # Update layout
        fig.update_layout(
            title_text=f"Test {self.number} - Distribution of Perceived Personality Traits (Histograms)",
            height=700,  # Increased height to accommodate better spacing
            showlegend=False
        )
        
        # Update axes with fixed range for all subplots
        for i in range(1, 6):  # 5 columns
            fig.update_xaxes(title_text="Score", range=[-1, 1], row=1, col=i)
            fig.update_xaxes(title_text="Score", range=[-1, 1], row=2, col=i)
        
        for i in range(1, 3):  # 2 rows
            fig.update_yaxes(title_text="Count", row=i, col=1)
        
        # Export to PNG and HTML
        png_filename = f"distributions-test-{self.number}.png"
        html_filename = f"distributions-test-{self.number}.html"
        try:
            fig.write_image(png_filename)
            print(f"Grafico delle distribuzioni salvato come: {png_filename}")
        except Exception as e:
            print(f"Errore nel salvare PNG distribuzioni: {e}")
        fig.write_html(html_filename)
        print(f"Grafico interattivo delle distribuzioni salvato come: {html_filename}")
        
        fig.show()

    def create_spider_plots(self, stats_mean, stats_var, counts):
        """Create spider/radar plots for each participant showing model vs perceived traits"""
        traits = ["Openness", "Carefulness", "Extraversion", "Amicability", "Neuroticism"]
        
        # Create subplot with polar coordinates
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "polar"}, {"type": "polar"}]]
            # Remove subplot_titles to avoid conflicts
        )
        
        colors = {'model': '#1f77b4', 'perceived': '#ff7f0e'}  # Blue for model, Orange for perceived
        
        # Alice (left)
        if counts["alice"] > 0:
            model_alice = [self.alice.o, self.alice.c, self.alice.e, self.alice.a, self.alice.n]
            perceived_alice = stats_mean["alice"]
            
            # Add model values (close the polygon by repeating first value)
            fig.add_trace(go.Scatterpolar(
                r=model_alice + [model_alice[0]],
                theta=traits + [traits[0]],
                fill='toself',
                fillcolor='rgba(31, 119, 180, 0.2)',
                line=dict(color=colors['model'], width=3),
                name='Model Alice'
            ), row=1, col=1)
            
            # Add perceived values
            fig.add_trace(go.Scatterpolar(
                r=perceived_alice + [perceived_alice[0]],
                theta=traits + [traits[0]],
                fill='toself',
                fillcolor='rgba(255, 127, 14, 0.2)',
                line=dict(color=colors['perceived'], width=3, dash='dash'),
                name='Perceived Alice'
            ), row=1, col=1)
        
        # Bob (right)
        if counts["bob"] > 0:
            model_bob = [self.bob.o, self.bob.c, self.bob.e, self.bob.a, self.bob.n]
            perceived_bob = stats_mean["bob"]
            
            # Add model values (close the polygon by repeating first value)
            fig.add_trace(go.Scatterpolar(
                r=model_bob + [model_bob[0]],
                theta=traits + [traits[0]],
                fill='toself',
                fillcolor='rgba(31, 119, 180, 0.2)',
                line=dict(color=colors['model'], width=3),
                name='Model Bob',
                showlegend=False  # Don't show duplicate legend entries
            ), row=1, col=2)
            
            # Add perceived values
            fig.add_trace(go.Scatterpolar(
                r=perceived_bob + [perceived_bob[0]],
                theta=traits + [traits[0]],
                fill='toself',
                fillcolor='rgba(255, 127, 14, 0.2)',
                line=dict(color=colors['perceived'], width=3, dash='dash'),
                name='Perceived Bob',
                showlegend=False  # Don't show duplicate legend entries
            ), row=1, col=2)
        
        # Update layout
        fig.update_layout(
            title_text=f"Test {self.number} - OCEAN Personality Traits (Spider Plot)",
            height=600,
            showlegend=True
        )
        
        # Update polar plots to have consistent range [-1, 1]
        fig.update_polars(
            radialaxis=dict(
                visible=True,
                range=[-1, 1],
                tickmode='linear',
                tick0=-1,
                dtick=0.5,
                gridcolor='lightgray'
            ),
            angularaxis=dict(
                tickfont_size=12,
                rotation=90,  # Start from top
                direction="clockwise"
            )
        )
        
        # Export to PNG and HTML
        png_filename = f"spider-test-{self.number}.png"
        html_filename = f"spider-test-{self.number}.html"
        try:
            fig.write_image(png_filename)
            print(f"Grafico spider salvato come: {png_filename}")
        except Exception as e:
            print(f"Errore nel salvare PNG spider: {e}")
        fig.write_html(html_filename)
        print(f"Grafico spider interattivo salvato come: {html_filename}")
        
        fig.show()

    def compute_stats( self ):
        # Create grouped bar charts (Model vs Perceived) for each participant
        traits = ["Openness", "Carefulness", "Extraversion", "Amicability", "Neuroticism"]

        # accumulate perceived scores, sums of squares and counts per participant
        stats_sum = {"alice": [0.0] * 5, "bob": [0.0] * 5}
        stats_sq = {"alice": [0.0] * 5, "bob": [0.0] * 5}
        counts = {"alice": 0, "bob": 0}

        for entry in self.entries:
            name = entry.name
            # compute per-entry trait vector (may combine multiple answers)
            vec = [0.0] * 5  # [O, C, E, A, N]
            valid = False
            # Q indices mapping into traits (with sign)
            # 0 -> Extraversion (negated), 1 -> Amicability, 2 -> Carefulness (negated),
            # 3 -> Neuroticism (negated), 4 -> Openness (negated), 5 -> Extraversion,
            # 6 -> Amicability (negated), 7 -> Carefulness, 8 -> Neuroticism, 9 -> Openness
            ans = [entry.get_ans(i) for i in range(10)]
            if ans[0] is not None:
                vec[2] += ans[0] * -1; valid = True
            if ans[1] is not None:
                vec[3] += ans[1]; valid = True
            if ans[2] is not None:
                vec[1] += ans[2] * -1; valid = True
            if ans[3] is not None:
                vec[4] += ans[3] * -1; valid = True
            if ans[4] is not None:
                vec[0] += ans[4] * -1; valid = True
            if ans[5] is not None:
                vec[2] += ans[5]; valid = True
            if ans[6] is not None:
                vec[3] += ans[6] * -1; valid = True
            if ans[7] is not None:
                vec[1] += ans[7]; valid = True
            if ans[8] is not None:
                vec[4] += ans[8]; valid = True
            if ans[9] is not None:
                vec[0] += ans[9]; valid = True

            if not valid:
                continue

            counts[name] += 1
            for i in range(5):
                normalized_score = vec[i] / 2  # Normalize to [-1, +1]
                stats_sum[name][i] += normalized_score
                stats_sq[name][i] += normalized_score * normalized_score

        # compute mean and variance per participant (population variance)
        stats_mean = {n: [0.0] * 5 for n in stats_sum}
        stats_var = {n: [0.0] * 5 for n in stats_sum}
        for name in stats_sum:
            if counts[name] == 0:
                continue
            stats_mean[name] = [s / counts[name] for s in stats_sum[name]]
            # variance = E[x^2] - (E[x])^2
            stats_var[name] = [stats_sq[name][i] / counts[name] - (stats_mean[name][i] ** 2) for i in range(5)]

        # Create a single figure with two subplots side-by-side (Alice | Bob)
        model_alice = [self.alice.o, self.alice.c, self.alice.e, self.alice.a, self.alice.n]
        perceived_alice = stats_mean.get("alice", [0.0] * 5)
        var_alice = stats_var.get("alice", [0.0] * 5)
        # Use variance (not std) for the error bars as requested
        err_alice = [v if v > 0 else 0.0 for v in var_alice]

        model_bob = [self.bob.o, self.bob.c, self.bob.e, self.bob.a, self.bob.n]
        perceived_bob = stats_mean.get("bob", [0.0] * 5)
        var_bob = stats_var.get("bob", [0.0] * 5)
        err_bob = [v if v > 0 else 0.0 for v in var_bob]

        # Put participant names above each subplot
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Alice", "Bob"))

        # Define consistent colors for Model and Perceived across both charts
        model_color = '#1f77b4'  # Blue
        perceived_color = '#ff7f0e'  # Orange

        # Alice (left)
        fig.add_trace(go.Bar(x=traits, y=model_alice, name="Model", 
                             marker_color=model_color), row=1, col=1)
        fig.add_trace(go.Bar(x=traits, y=perceived_alice, name="Perceived",
                             marker_color=perceived_color,
                             error_y=dict(type='data', array=err_alice, visible=True)), row=1, col=1)

        # Bob (right)
        fig.add_trace(go.Bar(x=traits, y=model_bob, name="Model", 
                             marker_color=model_color, showlegend=False), row=1, col=2)
        fig.add_trace(go.Bar(x=traits, y=perceived_bob, name="Perceived",
                             marker_color=perceived_color, showlegend=False,
                             error_y=dict(type='data', array=err_bob, visible=True)), row=1, col=2)

        fig.update_layout(title_text=f"Test {self.number}", barmode='group', showlegend=True)
        fig.update_yaxes(title_text='Score', row=1, col=1)
        fig.update_yaxes(title_text='Score', row=1, col=2)
        
        # Export to PNG and HTML
        png_filename = f"result-test-{self.number}.png"
        html_filename = f"result-test-{self.number}.html"
        try:
            fig.write_image(png_filename)
            print(f"Grafico salvato come: {png_filename}")
        except Exception as e:
            print(f"Errore nel salvare PNG: {e}")
        fig.write_html(html_filename)
        print(f"Grafico interattivo salvato come: {html_filename}")
        
        # Export analysis to Markdown
        self.export_to_markdown(stats_mean, stats_var, counts)
        
        # Create distribution plots
        self.create_distribution_plots(stats_mean, stats_var, counts)
        
        # Create spider/radar plots
        self.create_spider_plots(stats_mean, stats_var, counts)
        
        fig.show()

        # Print formatted statistics
        print(f"\nRESULTS ANALYSIS - Test {self.number}")
        print("=" * 80)
        
        # Header
        print(f"{'Trait':<15} {'Model':<8} {'Perceived':<10} {'Variance':<10} {'Distance':<10} {'Accuracy':<10}")
        print("-" * 80)
        
        trait_names = ["Openness", "Carefulness", "Extraversion", "Amicability", "Neuroticism"]
        
        for name in stats_mean:
            if counts[name] == 0:
                continue
                
            print(f"\n{name.upper()} (n={counts[name]} responses):")
            print("-" * 70)
            
            mean = stats_mean[name]
            var = stats_var[name]
            model_values = [getattr(self, name).o, getattr(self, name).c, 
                          getattr(self, name).e, getattr(self, name).a, getattr(self, name).n]
            
            total_distance = 0
            for i, trait in enumerate(trait_names):
                distance = abs(mean[i] - model_values[i])
                total_distance += distance
                accuracy = max(0, (1 - distance) * 100)  # Accuracy as percentage
                
                print(f"{trait:<15} {model_values[i]:<8.3f} {mean[i]:<10.3f} {var[i]:<10.3f} {distance:<10.3f} {accuracy:<9.1f}%")
            
            avg_distance = total_distance / 5
            avg_accuracy = max(0, (1 - avg_distance) * 100)
            print("-" * 70)
            print(f"{'AVERAGE':<15} {'':<8} {'':<10} {'':<10} {avg_distance:<10.3f} {avg_accuracy:<9.1f}%")
            print()

def load_entries( f : str ):
    entries = []
    data = pd.read_csv( f )
    for _, row in data.iterrows():
        found = False
        for i, suf in enumerate( SUFFIXES ):
            for lang in CHECK_FIELD:
                if found:
                    continue
                check_field = CHECK_FIELD[lang] + str( suf ) if suf > 1 else CHECK_FIELD[lang]
                if row[ check_field ] is not np.nan:
                    qs1 = []
                    qs2 = []
                    for q in Qs[lang]:
                        if suf == 1:
                            qs1.append( row[ q ] )
                        else:
                            qs1.append( row[ q + str(suf) ] )
                        qs2.append( row[ q + str(suf + 1) ] )
                    p1 = Entry( i+1, "alice", lang, qs1 )
                    p2 = Entry( i+1, "bob", lang, qs2 )
                    #! t = Test(suf, lang, p1, p2)
                    entries.append( p1 )
                    entries.append( p2 )
                    found = True
                    continue
    return entries 

def load_tests( f : str ):
    data = pd.read_csv( f )
    tests = {}
    for _, row in data.iterrows():
        if row[ "TestName" ] not in tests:
            tests[ row[ "TestName" ] ] = Test( row["TestName" ] ) 
        name = row[ "Agent" ]
        o = row[ "Openness" ] / 100
        c = row[ "Carefulness" ] / 100
        e = row[ "Extraversion" ] / 100
        a = row[ "Amicability" ] / 100
        n = row[ "Neuroticism" ] / 100
        p = Partecipant( name, o, c, e, a, n )
        tests[ row[ "TestName" ] ].add_partecipant( p )
    return tests
        

def main():
    print("\n" + "="*80)
    print("PERSONALITY PERCEPTION ANALYSIS")
    print("="*80)
    print("Loading data and analyzing personality perception accuracy...\n")
    
    tests = load_tests( "test.csv" )
    entries = load_entries( "results.csv" )
    
    print(f"Loaded {len(tests)} tests with {len(entries)} total responses\n")
    
    for entry in entries:
        tests[ entry.test ].add_entry( entry )
    
    for t in sorted(tests.keys()):
        print( tests[t] )
        tests[ t ].compute_stats()
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()