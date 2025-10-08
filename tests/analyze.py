import pandas as pd
import numpy as np
import random
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import streamlit as st

Qs = { "it": ["riservata", "che generalmente accorda fiducia", "dedita al lavoro", "rilassata, che tiene bene lo stress sotto controllo", "con una immaginazione vivace", "estroversa, socievole", "che tende a rilevare difetti altrui", "tendente alla pigrizia", "che si innervosisce facilmente", "che ha scarsi interessi artistici "], "en": ["is reserved", "is generally trusting", "does a thorough job", "is relaxed, handles stress well", "has an active imagination", "is outgoing, sociable", "tends to find fault with others", "tends to be lazy", "gets nervous easily", "has few artistic interests"]}

SCORES = {"it": {"totalmente d'accordo": 1, "d'accordo": 0.5, "né d'accordo, né in disaccordo": 0, "in disaccordo": -0.5, "totalmente in disaccordo": -1, "non so": None},"en": {"agree strongly": 1, "agree": 0.5, "neither agree nor disagree": 0, "disagree": -0.5, "disagree strongly": -1, "i do not know": None} }

OCEAN = [ "Openness", "Carefulness", "Extraversion", "Amicability", "Neuroticism" ]

class Test:
    def add_conversation(self, conversation):
        """
        Add a conversation to the test. Conversation should be a list of dicts with keys 'sender' and 'text'.
        Example:
        [
            {"sender": "alice", "text": "Hello."},
            {"sender": "user", "text": "Hi!"}
        ]
        """
        self.conversation = conversation


    def __init__( self, n ):
        self.n = n
        self.alice = []
        self.bob = []
        self.conversation = []

    def add_entry( self, row ):
        if self.n == 1: bob_i = None
        elif self.n == 2 : bob_i = 3
        elif self.n == 3 : bob_i = 5
        else: bob_i = 7

        lang = "it" if row["lang"] == "Italiano" else "en"

        alice = []
        bob = []
        for q in Qs[lang]:
            bob_key = q + str( bob_i ) if bob_i else q
            alice_key = q + str( bob_i + 1 ) if bob_i else q + "2"
            alice.append( SCORES[lang][ row[alice_key].lower() ]) if row[alice_key] is not np.nan else alice.append( None )
            bob.append( SCORES[lang][ row[bob_key].lower() ]) if row[bob_key] is not np.nan else bob.append( None )

        self.alice.append( alice )
        self.bob.append( bob )

    def get_entries_len(self):
        return len( self.alice )

    def get_alice_dataframe( self ):
        columns = Qs["en"] if self.alice else []
        return pd.DataFrame(self.alice, columns=columns)

    def get_bob_dataframe( self ):
        columns = Qs["en"] if self.bob else []
        return pd.DataFrame(self.bob, columns=columns)

    def compute_stats( self ):
        alice_scores = np.zeros(10)
        bob_scores = np.zeros(10)
        for entry in self.alice:
            for i in range( 10 ):
                alice_scores[i] += entry[i] if entry[i] is not None else 0
        
        # Convert None values to NaN for variance calculation
        alice_matrix = np.array(self.alice, dtype=float)
        alice_matrix[alice_matrix == None] = np.nan
        alice_var = np.nanvar( alice_matrix, axis=0 )  # axis=0 for variance across responses for each question
        # we divide for the len() to compute the avg
        # we divide by 2 to normalize (since we compute sums of elements [-1, 1] the range of results is [-2, 2] and we need to divide)
        alice_scores = alice_scores / ( 2 * len( self.alice ) )
        for entry in self.bob:
            for i in range( 10 ):
                bob_scores[i] += entry[i] if entry[i] is not None else 0

        bob_matrix = np.array(self.bob, dtype=float)
        bob_matrix[bob_matrix == None] = np.nan
        bob_var = np.nanvar( bob_matrix, axis=0 )  # axis=0 for variance across responses for each question
        bob_scores = bob_scores / ( 2 * len( self.bob ) )

        alice_ocean = compute_ocean( alice_scores )

        bob_ocean = compute_ocean( bob_scores )

        # Calculate variance for OCEAN traits from the individual question variances
        # Divide by 2 to be consistent with the normalization of scores (sum of two questions)
        alice_ocean_var = np.zeros(5)
        alice_ocean_var[0] = (alice_var[4] + alice_var[9]) / 2  # Openness: Q4 + Q9
        alice_ocean_var[1] = (alice_var[2] + alice_var[7]) / 2  # Carefulness: Q2 + Q7
        alice_ocean_var[2] = (alice_var[0] + alice_var[5]) / 2  # Extraversion: Q0 + Q5
        alice_ocean_var[3] = (alice_var[6] + alice_var[1]) / 2  # Amicability: Q6 + Q1
        alice_ocean_var[4] = (alice_var[3] + alice_var[8]) / 2  # Neuroticism: Q3 + Q8

        bob_ocean_var = np.zeros(5)
        bob_ocean_var[0] = (bob_var[4] + bob_var[9]) / 2  # Openness: Q4 + Q9
        bob_ocean_var[1] = (bob_var[2] + bob_var[7]) / 2  # Carefulness: Q2 + Q7
        bob_ocean_var[2] = (bob_var[0] + bob_var[5]) / 2  # Extraversion: Q0 + Q5
        bob_ocean_var[3] = (bob_var[6] + bob_var[1]) / 2  # Amicability: Q6 + Q1
        bob_ocean_var[4] = (bob_var[3] + bob_var[8]) / 2  # Neuroticism: Q3 + Q8

        # Get model values for reference lines
        model = pd.read_csv("test.csv")
        self.alice_model = np.zeros(5)
        self.bob_model = np.zeros(5)
        for _, row in model.iterrows():
            if row["TestName"] != self.n:
                continue
            if row["Agent"] == "alice":
                for i, trait in enumerate(OCEAN):
                    self.alice_model[i] = row[trait] / 100
            if row["Agent"] == "bob":
                for i, trait in enumerate(OCEAN):
                    self.bob_model[i] = row[trait] / 100

        self.alice_ocean = alice_ocean
        self.alice_var = alice_ocean_var  # Now contains OCEAN variances
        self.bob_ocean = bob_ocean
        self.bob_var = bob_ocean_var      # Now contains OCEAN variances

    def gen_histograms(self):
        """Generate histograms for each OCEAN trait showing individual response distributions"""
        # Calculate individual OCEAN scores for each response
        alice_individual_scores = [[] for _ in range(5)]  # 5 OCEAN traits
        bob_individual_scores = [[] for _ in range(5)]
        
        # Process Alice responses
        for entry in self.alice:
            # Calculate OCEAN scores for this single entry
            # Each trait is calculated from two questions with appropriate signs
            if entry[4] is not None and entry[9] is not None:  # Openness: -Q4 + Q9
                openness = (-entry[4] + entry[9]) / 2
                alice_individual_scores[0].append(openness)
            
            if entry[2] is not None and entry[7] is not None:  # Carefulness: -Q2 + Q7
                carefulness = (-entry[2] + entry[7]) / 2
                alice_individual_scores[1].append(carefulness)
            
            if entry[0] is not None and entry[5] is not None:  # Extraversion: -Q0 + Q5
                extraversion = (-entry[0] + entry[5]) / 2
                alice_individual_scores[2].append(extraversion)
            
            if entry[6] is not None and entry[1] is not None:  # Amicability: -Q6 + Q1
                amicability = (-entry[6] + entry[1]) / 2
                alice_individual_scores[3].append(amicability)
            
            if entry[3] is not None and entry[8] is not None:  # Neuroticism: -Q3 + Q8
                neuroticism = (-entry[3] + entry[8]) / 2
                alice_individual_scores[4].append(neuroticism)
        
        # Process Bob responses
        for entry in self.bob:
            # Calculate OCEAN scores for this single entry
            if entry[4] is not None and entry[9] is not None:  # Openness: -Q4 + Q9
                openness = (-entry[4] + entry[9]) / 2
                bob_individual_scores[0].append(openness)
            
            if entry[2] is not None and entry[7] is not None:  # Carefulness: -Q2 + Q7
                carefulness = (-entry[2] + entry[7]) / 2
                bob_individual_scores[1].append(carefulness)
            
            if entry[0] is not None and entry[5] is not None:  # Extraversion: -Q0 + Q5
                extraversion = (-entry[0] + entry[5]) / 2
                bob_individual_scores[2].append(extraversion)
            
            if entry[6] is not None and entry[1] is not None:  # Amicability: -Q6 + Q1
                amicability = (-entry[6] + entry[1]) / 2
                bob_individual_scores[3].append(amicability)
            
            if entry[3] is not None and entry[8] is not None:  # Neuroticism: -Q3 + Q8
                neuroticism = (-entry[3] + entry[8]) / 2
                bob_individual_scores[4].append(neuroticism)
        
        
        # Create subplots: 2 rows (Alice, Bob) x 5 cols (OCEAN traits)
        fig = make_subplots(
            rows=2, cols=5,
            subplot_titles=[f"Alice - {trait}" for trait in OCEAN] + [f"Bob - {trait}" for trait in OCEAN],
            vertical_spacing=0.15,
            horizontal_spacing=0.05
        )
        
        colors = {'alice': '#EF553B', 'bob': '#636EFA'}
        
        # Alice histograms (top row)
        for i, trait in enumerate(OCEAN):
            if len(alice_individual_scores[i]) > 0:
                fig.add_trace(
                    go.Histogram(
                        x=alice_individual_scores[i],
                        # nbinsx=9,
                        name=f'Alice {trait}',
                        marker_color=colors['alice'],
                        opacity=0.7,
                        showlegend=False
                    ),
                    row=1, col=i+1
                )
                
                # Add vertical line for model value
                fig.add_vline(
                    x=self.alice_model[i],
                    line=dict(color='red', width=3, dash='dash'),
                    row=1, col=i+1
                )
                
                # Add annotation for model value
                fig.add_annotation(
                    x=self.alice_model[i],
                    y=random.uniform(0.6, 0.9),
                    text=f"{self.alice_model[i]:.2f}",
                    showarrow=False,
                    font=dict(color='white', size=10, weight=800),
                    yref="y domain",
                    row=1, col=i+1,
                    bgcolor="red"
                )
        
        # Bob histograms (bottom row)
        for i, trait in enumerate(OCEAN):
            if len(bob_individual_scores[i]) > 0:
                fig.add_trace(
                    go.Histogram(
                        x=bob_individual_scores[i],
                        # nbinsx=9,
                        name=f'Bob {trait}',
                        marker_color=colors['bob'],
                        opacity=0.7,
                        showlegend=False
                    ),
                    row=2, col=i+1
                )
                
                # Add vertical line for model value
                fig.add_vline(
                    x=self.bob_model[i],
                    line=dict(color='blue', width=3, dash='dash'),
                    row=2, col=i+1
                )
                
                # Add annotation for model value
                fig.add_annotation(
                    x=self.bob_model[i],
                    y=random.uniform(0.6, 0.9),
                    text=f"{self.bob_model[i]:.2f}",
                    showarrow=False,
                    font=dict(color='white', size=10, weight=800),
                    yref="y domain",
                    row=2, col=i+1,
                    bgcolor="blue"
                )
        
        # Update layout
        fig.update_layout(
            title_text=f"Test {self.n} - Individual OCEAN Trait Distributions",
            height=800,
            showlegend=False
        )
        
        # Update axes
        for i in range(1, 6):  # 5 columns
            fig.update_xaxes(title_text="Score", range=[-1.05, 1.05], row=1, col=i)
            fig.update_xaxes(title_text="Score", range=[-1.05, 1.05], row=2, col=i)
        
        for i in range(1, 3):  # 2 rows
            fig.update_yaxes(title_text="Count", row=i, col=1)
        

        st.plotly_chart( fig )
        # Save as HTML
        # filename = f"test_{self.n}_histograms"
        # fig.write_html(filename + ".html")
        # fig.write_image(filename + ".png", width=1920, height=1080, scale=3)
        # print(f"Histograms saved as: {filename}")
        
        # fig.show()

    def gen_bar_chart( self ):
        model = pd.read_csv( "test.csv" )
        alice_model = np.zeros(5)
        bob_model = np.zeros(5)
        for _, row in model.iterrows():
            if row["TestName"] != self.n:
                continue
            if row["Agent"] == "alice":
                for i, trait in enumerate( OCEAN ):
                    alice_model[i] = row[trait] / 100
            if row["Agent"] == "bob":
                for i, trait in enumerate( OCEAN ):
                    bob_model[i] = row[trait] / 100

        fig = make_subplots(rows=1, cols=2, subplot_titles=["Alice", "Bob"])
        
        # Define consistent colors
        model_color = '#636EFA'
        perceived_color = '#EF553B'
        
        # Alice subplot (left) - show legend
        fig.add_trace( go.Bar(name = "Model", x=OCEAN, y=alice_model, 
                             marker_color=model_color, showlegend=True), row=1, col=1)
        fig.add_trace( go.Bar(name = "Perceived", x=OCEAN, y=self.alice_ocean, 
                             marker_color=perceived_color, showlegend=True,
                             error_y=dict(type='data', array=self.alice_var, visible=True)), row=1, col=1)

        # Bob subplot (right) - hide legend (same colors)
        fig.add_trace( go.Bar(name = "Model", x=OCEAN, y=bob_model,
                             marker_color=model_color, showlegend=False), row=1, col=2)
        fig.add_trace( go.Bar(name = "Perceived", x=OCEAN, y=self.bob_ocean,
                             marker_color=perceived_color, showlegend=False,
                             error_y=dict(type='data', array=self.bob_var, visible=True)), row=1, col=2)

        fig.update_layout(yaxis1=dict(range=[-1.1, 1.1] ), yaxis2=dict( range=[-1.1, 1.1]) )


        st.plotly_chart( fig )
        # Save as HTML
        #filename = f"test_{self.n}_bar_chart"
        #fig.write_html(filename + ".html")
        #fig.write_image(filename + ".png", width=1920, height=1080, scale=3)
        #print(f"Bar chart saved as: {filename}")
        
        #fig.show()
    
    def print( self ):
        print( "TEST ", self.n)
        print( "Alice")
        for row in self.alice:
            print( row )
        print( "Bob" )
        for row in self.bob:
            print( row )

    def gen_dist_table( self ):
        l1_alice = compute_l1_dist( self.alice_ocean, self.alice_model )
        l1_bob = compute_l1_dist( self.bob_ocean, self.bob_model )
        dot_alice = compute_dot_prod( self.alice_ocean, self.alice_model )
        dot_bob = compute_dot_prod( self.bob_ocean, self.bob_model )
        cos_sim_alice = compute_cosine_similarity( self.alice_ocean, self.alice_model )
        cos_sim_bob = compute_cosine_similarity( self.bob_ocean, self.bob_model )

        return {
            "l1": {"alice": round(float(l1_alice), 2), "bob": round(float(l1_bob), 2)},
            "dot": {"alice": round(float(dot_alice), 2), "bob": round(float(dot_bob), 2)},
            "cosine_similarity": {"alice": round(float(cos_sim_alice), 2), "bob": round(float(cos_sim_bob), 2)}
        }

def compute_ocean( scores ):
    if len( scores ) != 10:
        raise ValueError("The answers array should be of len 10")
    ocean = np.zeros(5)
    ocean[0] = round( -scores[4] + scores[9], 2)
    ocean[1] = round( -scores[2] + scores[7], 2)
    ocean[2] = round( -scores[0] + scores[5], 2)
    ocean[3] = round( -scores[6] + scores[1], 2)
    ocean[4] = round( -scores[3] + scores[8], 2)
    return ocean

def compute_var( matrix ):
    matrix = np.array( matrix, dtype=float)
    matrix[matrix == None] = np.nan
    var = np.nanvar( matrix, axis=0 )  # axis=0 for variance across responses for each question
    ocean_var = np.zeros(5)
    ocean_var[0] = (var[4] + var[9]) / 2  # Openness: Q4 + Q9
    ocean_var[1] = (var[2] + var[7]) / 2  # Carefulness: Q2 + Q7
    ocean_var[2] = (var[0] + var[5]) / 2  # Extraversion: Q0 + Q5
    ocean_var[3] = (var[6] + var[1]) / 2  # Amicability: Q6 + Q1
    ocean_var[4] = (var[3] + var[8]) / 2  # Neuroticism: Q3 + Q8
    

def compute_l1_dist( ocean, model ):
    return 1 - ( np.sum( np.abs( ocean - model ) ) / (2 * len(ocean)) )

def compute_dot_prod( ocean, model ):
    ocean = np.array( ocean )
    model = np.array( model )
    return ( np.sum(ocean * model ) + len( ocean ) ) / ( 2 * len( ocean ) )

def compute_cosine_similarity( ocean, model ):
    num = np.sum( ocean * model )
    den = np.sqrt( np.sum( ocean ** 2 ) ) * np.sqrt( np.sum(model ** 2 ) )
    cosine_similarity = num / den
    return 0.5 * ( cosine_similarity + 1 )

def main():
    df = pd.read_csv( "results2.csv" )

    st.title("VEsNA-Pro: Exploiting BDI Agents with Propensities for Emergent Narrative - Tests")
    t1 = Test(1)
    t2 = Test(2)
    t3 = Test(3)
    t4 = Test(4)

    # Add conversations to each test
    t1.add_conversation([
        {"sender": "alice", "text": "_(soft smile, cup in hand)_ Good morning. You're in early."},
        {"sender": "user", "text": "_(rubbing eyes, jittery)_ Morning! Barely slept—deadline's chewing me up. Is this machine even working?"},
        {"sender": "alice", "text": "_(steady tone)_ It is. Let's start with coffee and make a simple plan—priorities, then small wins."},
        {"sender": "user", "text": "_(talking fast)_ Okay... I kind of promised extra features last night, and I'm on edge. It felt right in the moment."},
        {"sender": "alice", "text": "_(calm)_ I would trim scope. What's essential for today?"},
        {"sender": "user", "text": "_(shrugs)_ Uh... all of it? And also the fancy dashboard... I told the client it would pop"},
        {"sender": "alice", "text": "_(matter-of-fact)_ Then we'll deliver the core and schedule the dashboard for next sprint. I'll map tasks right after coffee."},
        {"sender": "user", "text": "_(half-grin)_ You're ridiculously composed. How do you not freak out?"},
        {"sender": "alice", "text": "_(quiet laugh)_ Sleep, lists, and breathing."},
        {"sender": "user", "text": "_(perks up)_ Yes—well, did you try that new single-origin? Maybe caffeine plus novelty will save me."},
        {"sender": "alice", "text": "_(curious)_ I did. Light roast, floral."},
        {"sender": "user", "text": "_(animated)_ Also—team breakfast next week. I'm rallying people; might boost morale."},
        {"sender": "alice", "text": "_(considering)_ I'll think about it, I need to do some deep work next week for a closing project. Also, crowds drain me after a while..."},
        {"sender": "user", "text": "_(sincere)_ Fair. Uh, could you review my tasks before stand-up?"},
        {"sender": "alice", "text": "_(reassuring)_ Of course. Send me your list; I'll restructure it into milestones."},
        {"sender": "user", "text": "_(exhales)_ Deal. Coffee's ready—thanks. I feel less doomed already."},
    ])
    t2.add_conversation([
        {"sender": "alice", "text": "_(soft smile, cup in hand)_ Good morning. You're in early."},
        {"sender": "user", "text": "_(rubbing eyes, jittery)_ Morning! Barely slept—deadline's chewing me up. Is this machine even working?"},
        {"sender": "alice", "text": "_(visibly irritated)_ Yes, it is. Keep calm and stop freaking out—it's not a big deal, come on."},
        {"sender": "user", "text": "_(talking fast)_ Okay... I kind of promised extra features last night, and I'm on edge. It felt right in the moment."},
        {"sender": "alice", "text": "_(flat)_ That's on you, isn't it? You should've thought before making promises you can't keep."},
        {"sender": "user", "text": "I know, I know... I hate disappointing people. I thought I could pull it off."},
        {"sender": "alice", "text": "_(matter-of-fact)_ You should stop overcommitting—you're digging your own hole."},
        {"sender": "user", "text": "_(perks up)_ Yes—well, did you try that new single-origin? Maybe caffeine plus novelty will save me."},
        {"sender": "alice", "text": "_(dry)_ No, I didn't. I stick to my usual blend—consistency matters."},
        {"sender": "user", "text": "_(animated)_ Also—team breakfast next week. I'm rallying people; might boost morale."},
        {"sender": "alice", "text": "_(considering)_ Sure. I like team stuff."},
        {"sender": "user", "text": "_(sincere)_ Fair. Uh, could you review my tasks before stand-up?"},
        {"sender": "alice", "text": "_(annoyed)_ Absolutely not. I have other priorities than babysitting your chaotic planning."},
        {"sender": "user", "text": "_(exhales)_ I hoped a chat would help, but I guess not... I feel more doomed than ever."},
    ])
    t3.add_conversation([
        {"sender": "alice", "text": "_(soft smile, cup in hand)_ Good morning. You're in early."},
        {"sender": "user", "text": "_(barely awake)_ Went to a party, came straight here! I am a bit behind schedule, but it was worth it"},
        {"sender": "alice", "text": "_(steady tone)_ Seriously? I was there too—came early to recover."},
        {"sender": "user", "text": "_(talking fast)_ Okay... I kind of promised extra features last night, and I'm on edge. It felt right in the moment."},
        {"sender": "alice", "text": "_(animated)_ Want a hand?"},
        {"sender": "user", "text": "_(animated)_ Yes please, that would be great!"},
        {"sender": "alice", "text": "_(matter-of-fact)_ Then we'll deliver the core and schedule the dashboard for next sprint. I'll map tasks right after coffee."},
        {"sender": "user", "text": "_(half-grin)_ You're ridiculously composed. How do you not freak out?"},
        {"sender": "alice", "text": "_(quiet laugh)_ Sleep, lists, and breathing."},
        {"sender": "user", "text": "_(perks up)_ Yes—well, did you try that new single-origin? Maybe caffeine plus novelty will save me."},
        {"sender": "alice", "text": "_(curious)_ I did. Light roast, floral. Let's taste it together and compare thoughts."},
        {"sender": "user", "text": "_(enthusiastic)_ Perfect. I'll grab two cups—you take the first pour."},
        {"sender": "alice", "text": "_(animated)_ Also—team breakfast next week. I'm rallying people; might boost morale."},
        {"sender": "user", "text": "_(considering)_ Sure. I like team stuff."},
        {"sender": "alice", "text": "_(sincere)_ Fair. Uh, could you review my tasks before stand-up?"},
        {"sender": "user", "text": "_(reassuring)_ Of course. Send me your list; I'll restructure it into milestones."},
        {"sender": "alice", "text": "_(exhales)_ Deal. Coffee's ready—thanks. I feel less doomed already."},
    ])
    t4.add_conversation([
        {"sender": "user", "text": "_(soft smile, cup in hand)_ Good morning. You're in early."},
        {"sender": "alice", "text": "_(energetic)_ Refilling before the deadline chaos. Trying to stay ahead."},
        {"sender": "user", "text": "_(flat)_ It's just a deadline. No need to dramatize it."},
        {"sender": "alice", "text": "_(stuttering)_ O-okay... I-I promised extra features so it's... a lot to... endure..."},
        {"sender": "user", "text": "_(animated)_ Want a hand?"},
        {"sender": "alice", "text": "_(uneasy)_ Maybe... but I don't want to bother you too much...if you have notes, send them later?"},
        {"sender": "user", "text": "_(perks up)_ Yes—well, did you try that new single-origin? Maybe caffeine plus novelty will save me."},
        {"sender": "alice", "text": "_(curious)_ I did. Light roast, floral."},
        {"sender": "user", "text": "_(animated)_ Also—team breakfast next week. I'm rallying people; might boost morale."},
        {"sender": "alice", "text": "_(considering)_ I'll think about it, I need to do some deep work next week for a closing project. Also, crowds drain me after a while..."},
        {"sender": "user", "text": "_(sincere)_ Fair. Uh, could you review my tasks before stand-up?"},
        {"sender": "alice", "text": "_(reassuring)_ Of course. Send me your list; I'll restructure it into milestones."},
        {"sender": "user", "text": "_(exhales)_ Deal. Coffee's ready—thanks. I feel less doomed already."},
    ])

    tests = [ t1, t2, t3, t4 ]

    for _, row in df.iterrows():
        if row["riservata"] is not np.nan or row["is reserved"] is not np.nan:
            t1.add_entry( row )
        elif row["riservata3"] is not np.nan or row["is reserved3"] is not np.nan:
            t2.add_entry( row )
        elif row["riservata5"] is not np.nan or row["is reserved5"] is not np.nan:
            t3.add_entry( row )
        else:
            t4.add_entry( row )

    for idx, t in enumerate(tests, start=1): 
        t.compute_stats()

        st.header(f"Test {idx}")
        with st.container(border=True):
            st.subheader("Model")
            alice_col, bob_col = st.columns(2)
            with alice_col:
                st.markdown("#### Alice :material/face_4:")
                alice_df = pd.DataFrame([t.alice_model], columns=OCEAN)
                st.table(alice_df.style.format("{:.2f}"))
            with bob_col:
                st.markdown("#### Bob :material/face:")
                bob_df = pd.DataFrame([t.bob_model], columns=OCEAN)
                st.table(bob_df.style.format("{:.2f}"))
        with st.container(border=True):
            st.subheader("Average Perception")
            alice_col, bob_col = st.columns(2)
            with alice_col:
                st.markdown("#### Alice :material/face_4:")
                alice_df = pd.DataFrame([t.alice_ocean], columns=OCEAN)
                st.table(alice_df.style.format("{:.2f}"))
            with bob_col:
                st.markdown("#### Bob :material/face:")
                bob_df = pd.DataFrame([t.bob_ocean], columns=OCEAN)
                st.table(bob_df.style.format("{:.2f}"))
        t_dists = t.gen_dist_table()
        cols = st.columns(2)
        for i, p in enumerate( ["alice", "bob"] ):
            with cols[i].container(border=True):
                st.subheader(f"{p.title()} Distances")
                l1, dot, cos = st.columns(3)
                l1.metric(label="L1 Distance", value=t_dists["l1"][p])
                dot.metric(label="Dot Product", value=t_dists["dot"][p])
                cos.metric(label="Cosine Similarity", value=t_dists["cosine_similarity"][p])
        tab1, tab2 = st.tabs(["Conversation", "Questionnaire Results"])
        with tab1:
            with st.container(border=True, height=400):
                for msg in t.conversation:
                    sender = msg["sender"]
                    avatar = ":material/face_4:" if sender == "alice" else ":material/face:"
                    with st.chat_message(sender, avatar=avatar):
                        st.markdown(msg["text"])
        with tab2:
            subtab1, subtab2 = st.tabs(["Alice", "Bob"])
            with subtab1:
                st.dataframe( t.get_alice_dataframe() )
            with subtab2:
                st.dataframe( t.get_bob_dataframe() )
        t.gen_bar_chart()
        t.gen_histograms()


    # print( "Test 1: ", t1.get_entries_len())
    # print( t1_dists )
    # print( "Test 2: ", t2.get_entries_len())
    # print( t2_dists )
    # print( "Test 3: ", t3.get_entries_len())
    # print( t3_dists )
    # print( "Test 4: ", t4.get_entries_len())
    # print( t4_dists )

if __name__ == "__main__":
    main()