import pandas as pd
import numpy as np

Qs = { "it": ["riservata", "che generalmente accorda fiducia", "dedita al lavoro", "rilassata, che tiene bene lo stress sotto controllo", "con una immaginazione vivace", "estroversa, socievole", "che tende a rilevare difetti altrui", "tendente alla pigrizia", "che si innervosisce facilmente", "che ha scarsi interessi artistici "], "en": ["is reserved", "is generally trusting", "does a thorough job", "is relaxed, handles stress well", "has an active imagination", "is outgoing, sociable", "tends to find fault with others", "tends to be lazy", "gets nervous easily", "has few artistic interests"]}

SCORES = {"it": {"totalmente d'accordo": 1, "d'accordo": 0.5, "né d'accordo, né in disaccordo": 0, "in disaccordo": -0.5, "totalmente in disaccordo": -1, "non so": None},"en": {"agree strongly": 1, "agree": 0.5, "neither agree nor disagree": 0, "disagree": -0.5, "disagree strongly": -1, "i do not know": None} }

class Test:


    def __init__( self, n ):
        self.n = n
        self.alice = []
        self.bob = []

    def add_entry( self, row ):
        if self.n == 1: alice_i = None
        elif self.n == 2 : alice_i = 3
        elif self.n == 3 : alice_i = 5
        else: alice_i = 7

        lang = "it" if row["lang"] == "Italiano" else "en"

        alice = []
        bob = []
        for q in Qs[lang]:
            alice_key = q + str( alice_i ) if alice_i else q
            bob_key = q + str( alice_i + 1 ) if alice_i else q + "2"
            alice.append( SCORES[lang][ row[alice_key].lower() ]) if row[alice_key] is not np.nan else None
            bob.append( SCORES[lang][ row[bob_key].lower() ]) if row[bob_key] is not np.nan else None
        self.alice.append( alice )
        self.bob.append( bob )

    def compute_stats( self ):
        alice_scores = np.zeros(10)
        bob_scores = np.zeros(10)
        for entry in self.alice:
            print( "SCORE", alice_scores )
            print( "ENTRY", entry )
            for i in range( 10 ):
                alice_scores[i] += entry[i] if entry[i] is not None else 0
        print( alice_scores/len( self.alice)*100)
        print( "=== BOB ===")
        for entry in self.bob:
            print( "SCORE", bob_scores )
            print( "ENTRY", entry )
            for i in range( 10 ):
                bob_scores[i] += entry[i] if entry[i] is not None else 0
        print( bob_scores/len( self.alice)*100)
    
    def print( self ):
        print( "TEST ", self.n)
        print( "Alice")
        for row in self.alice:
            print( row )
        print( "Bob" )
        for row in self.bob:
            print( row )



def main():
    df = pd.read_csv( "results2.csv" )
    t1 = Test(1)
    t2 = Test(2)
    t3 = Test(3)
    t4 = Test(4)

    for _, row in df.iterrows():
        if row["riservata"] is not np.nan or row["is reserved"] is not np.nan:
            t1.add_entry( row )
        elif row["riservata3"] is not np.nan or row["is reserved3"] is not np.nan:
            t2.add_entry( row )
        elif row["riservata5"] is not np.nan or row["is reserved5"] is not np.nan:
            t3.add_entry( row )
        else:
            t4.add_entry( row )
        
    t1.print()
    t1.compute_stats()

if __name__ == "__main__":
    main()