mdp

// probabilities
const double infect=0.5; // probability virus infects a node
const double detect1=0.5; // probability virus detected by firewall of high/low node
const double detect2=0.8; // probability virus detected by firewall of barrier node

// low nodes (those above the ceil(N/2) row)

const double detect11=detect1;
const double detect12=detect1;
const double detect13=detect1;

// barrier nodes (those in the ceil(N/2) row)

const double detect21=detect2;
const double detect22=detect2;
const double detect23=detect2;

// high nodes (those below the ceil(N/2) row)

const double detect31=detect1;
const double detect32=detect1;
const double detect33=detect1;




const int X33_23 = 1;
const int X22_21 = 1;

const int X2333_32 = 1;
const int X2333_13 = 0;
const int X2333_22 = 2;

const int X3233_23 = 0;
const int X3233_31 = 1;
const int X3233_22 = 2;

const int X132333_32 = 0;
const int X132333_12 = 2;
const int X132333_22 = 1;

const int X313233_23 = 0;
const int X313233_21 = 2;
const int X313233_22 = 1;

const int X233233_31 = 0;
const int X233233_13 = 1;
const int X233233_22 = 2;

const int X23313233_13 = 2;
const int X23313233_21 = 1;
const int X23313233_22 = 0;

const int X13233233_12 = 0;
const int X13233233_31 = 2;
const int X13233233_22 = 1;

const int X1323313233_12 = 0;
const int X1323313233_21 = 2;
const int X1323313233_22 = 1;


module strategy
    step : [0..2] init 0;
    l :  [0..1] init 0;

    // Alternate between horizontal and vertical attack. Unclear how to start.
    [attack23_33] step=0 & s33 = 2 & s11 != 2 & s21 != 2 & s31 != 2 & s12 != 2 & s22 != 2 & s32 != 2 & s13 != 2 & s23 != 2 & l=X33_23 -> (step'=1) & (l'=1-l);
    [attack32_33] step=0 & s33 = 2 & s11 != 2 & s21 != 2 & s31 != 2 & s12 != 2 & s22 != 2 & s32 != 2 & s13 != 2 & s23 != 2 & l=1-X33_23 -> (step'=1) & (l'=1-l);

    // This part is clear. We just attack target if possible.
    [attack11_21] step=0 & s21 = 2 -> (step'=1);
    [attack11_12] step=0 & s12 = 2 -> (step'=1);

    [attack13_12] false -> true;
    [attack23_22] false -> true;
    [attack31_21] false -> true;
    [attack32_22] false -> true;


    // This part is also rather clear, we just have to decide whether we attack horizontal or vertical. No need to attack a non-neighbour.
    [attack21_22] step=0 & s22 = 2 & l=X22_21 -> (step'=1) & (l'=1-l);
    [attack12_22] step=0 & s22 = 2 & l=1-X22_21 -> (step'=1) & (l'=1-l);

    // s33 and s23
    [attack32_33] step=0 & s23 = 2 & s22 != 2 & s32 != 2 & s13 != 2 & l=X2333_32 -> (step'=1) & (l'=1-l);
    [attack13_23] step=0 & s23 = 2 & s22 != 2 & s32 != 2 & s13 != 2 & l=X2333_13 -> (step'=1) & (l'=1-l);
    [attack22_23] step=0 & s23 = 2 & s22 != 2 & s32 != 2 & s13 != 2 & l=X2333_22 -> (step'=1) & (l'=1-l);

    // s33 and s32
    [attack23_33] step=0 & s32 = 2 & s22 != 2 & s23 != 2 & s31 != 2 & l=X3233_23 -> (step'=1) & (l'=1-l);
    [attack31_32] step=0 & s32 = 2 & s22 != 2 & s23 != 2 & s31 != 2 & l=X3233_31 -> (step'=1) & (l'=1-l);
    [attack22_32] step=0 & s32 = 2 & s22 != 2 & s23 != 2 & s31 != 2 & l=X3233_22 -> (step'=1) & (l'=1-l);

    // s33 and s23 and s13
    [attack32_33] step=0 & s13 = 2 & s22 != 2 & s32 != 2 & s12 != 2 & l=X132333_32 -> (step'=1) & (l'=1-l);
    [attack12_13] step=0 & s13 = 2 & s22 != 2 & s32 != 2 & s12 != 2 & l=X132333_12 -> (step'=1) & (l'=1-l);
    [attack22_23] step=0 & s13 = 2 & s22 != 2 & s32 != 2 & s12 != 2 & l=X132333_22 -> (step'=1) & (l'=1-l);

    // s33 and s32 and s31
    [attack23_33] step=0 & s31 = 2 & s22 != 2 & s23 != 2 & s12 != 2 & l=X313233_23 -> (step'=1) & (l'=1-l);
    [attack21_31] step=0 & s31 = 2 & s22 != 2 & s23 != 2 & s12 != 2 & l=X313233_21 -> (step'=1) & (l'=1-l);
    [attack22_32] step=0 & s31 = 2 & s22 != 2 & s23 != 2 & s12 != 2 & l=X313233_22 -> (step'=1) & (l'=1-l);


    // s33 and s32 and s23
    [attack31_32] step=0 & s32 = 2 & s23 = 2 & s22 != 2 & s31 != 2 & s12 != 2 & l=X233233_31 -> (step'=1) & (l'=1-l);
    [attack13_23] step=0 & s32 = 2 & s23 = 2 & s22 != 2 & s31 != 2 & s12 != 2 & l=X233233_13 -> (step'=1) & (l'=1-l);
    [attack22_32] step=0 & s32 = 2 & s23 = 2 & s22 != 2 & s31 != 2 & s12 != 2 & l=X233233_22 -> (step'=1) & (l'=1-l);


    // s33 and s32 and s31 and s23
    [attack13_23] step=0 & s31 = 2 & s23 = 2 & s22 != 2 & s21 != 2 & s13 != 2 & l=X23313233_13 -> (step'=1) & (l'=1-l);
    [attack21_31] step=0 & s31 = 2 & s23 = 2 & s22 != 2 & s21 != 2 & s13 != 2 & l=X23313233_21 -> (step'=1) & (l'=1-l);
    [attack22_23] step=0 & s31 = 2 & s23 = 2 & s22 != 2 & s21 != 2 & s13 != 2 & l=X23313233_22 -> (step'=1) & (l'=1-l);


    // s33 and s32 and s13 and s23
    [attack12_13] step=0 & s13 = 2 & s32 = 2 & s22 != 2 & s31 != 2 & s12 != 2 & l=X13233233_12 -> (step'=1) & (l'=1-l);
    [attack31_32] step=0 & s13 = 2 & s32 = 2 & s22 != 2 & s31 != 2 & s12 != 2 & l=X13233233_31 -> (step'=1) & (l'=1-l);
    [attack22_23] step=0 & s13 = 2 & s32 = 2 & s22 != 2 & s31 != 2 & s12 != 2 & l=X13233233_22 -> (step'=1) & (l'=1-l);

    // s33 and s32 and s31 and s23 and s13
    [attack12_13] step=0 & s31 = 2 & s13 = 2 & s22 != 2 & s21 != 2 & s12 != 2 & l=X1323313233_12 -> (step'=1) & (l'=1-l);
    [attack21_31] step=0 & s31 = 2 & s13 = 2 & s22 != 2 & s21 != 2 & s12 != 2 & l=X1323313233_21 -> (step'=1) & (l'=1-l);
    [attack22_23] step=0 & s31 = 2 & s13 = 2 & s22 != 2 & s21 != 2 & s12 != 2 & l=X1323313233_22 -> (step'=1) & (l'=1-l);


    [eval] (step=1) -> (step'=2);
    [report] step=2 & (s11=4 | s12 = 4 | s13 = 4 | s21 = 4 | s22 = 4 | s23 = 4 | s31 = 4 | s32 = 4 | s33 = 4) ->  (step'=0) & (l'=0);
    [report] step=2 & !(s11=4 | s12 = 4 | s13 = 4 | s21 = 4 | s22 = 4 | s23 = 4 | s31 = 4 | s32 = 4 | s33 = 4) -> (step'=0);

    [] s11 = 2 -> true;
endmodule


// first column (1..N)
module n11

	s11 : [0..4]; // node uninfected
	// 0 - node uninfected
	// 1 - node uninfected but firewall breached
	// 2 - node infected
    // 3 - save mode
    // 4 - infection taking place right now.

	// firewall attacked (from an infected neighbour)
	[attack11_21] (s11=0) ->  detect11 : true + (1-detect11) : (s11'=1);
	[attack11_12] (s11=0) ->  detect11 : true + (1-detect11) : (s11'=1);
	// if the firewall has been breached tries to infect the node
	[eval] (s11=1) -> infect : (s11'=4) + (1-infect) : (s11'=3);
	// restore save mode
	[eval] (s11=3) -> (s11'=0);
	// never block eval.
	[eval] (s11!=1) & (s11!=3) -> true;

	[report] (s11=4) -> (s11'=2);
  [report] (s11!=4) -> true;
	// if the node is infected, then it tries to attack its neighbouring nodes
	[attack21_11] (s11=2) -> true;
	[attack12_11] (s11=2) -> true;

endmodule

module n21

	s21 : [0..4]; // node uninfected
	// 0 - node uninfected
	// 1 - node uninfected but firewall breached
	// 2 - node infected

	// firewall attacked (from an infected neighbour)
	[attack21_31] (s21=0) -> detect21 : true + (1-detect21) : (s21'=1);
	[attack21_22] (s21=0) -> detect21 : true + (1-detect21) : (s21'=1);
	[attack21_11] (s21=0) -> detect21 : true + (1-detect21) : (s21'=1);
	// if the firewall has been breached tries to infect the node
	[eval] (s21=1) -> infect : (s21'=4) + (1-infect) : (s21'=3);
	// restore save mode
	[eval] (s21=3) -> (s21'=0);
	// never block eval.
	[eval] (s21!=1) & (s21!=3) -> true;
  [report] (s21=4) -> (s21'=2);
  [report] (s21!=4) -> true;

	// if the node is infected, then it tries to attack its neighbouring nodes
	[attack31_21] (s21=2) -> true;
	[attack22_21] (s21=2) -> true;
	[attack11_21] (s21=2) -> true;

endmodule

module n31=n11[s11=s31,detect11=detect31,attack21_11=attack21_31,attack12_11=attack32_31,attack11_21=attack31_21,attack11_12=attack31_32] endmodule

// second column
module n12=n21[s21=s12,detect21=detect12,attack31_21=attack13_12,attack22_21=attack22_12,attack11_21=attack11_12,attack21_31=attack12_13,attack21_22=attack12_22,attack21_11=attack12_11] endmodule

module n22

	s22 : [0..4]; // node uninfected
	// 0 - node uninfected
	// 1 - node uninfected but firewall breached
	// 2 - node infected

	// firewall attacked (from an infected neighbour)
	[attack22_32] (s22=0) -> detect22 : true + (1-detect22) : (s22'=1);
	[attack22_23] (s22=0) -> detect22 : true + (1-detect22) : (s22'=1);
	[attack22_12] (s22=0) -> detect22 : true + (1-detect22) : (s22'=1);
	[attack22_21] (s22=0) -> detect22 : true + (1-detect22) : (s22'=1);
	// if the firewall has been breached tries to infect the node
	[eval] (s22=1) -> infect : (s22'=4) + (1-infect) : (s22'=3);
	// restore save mode
	[eval] (s22=3) -> (s22'=0);
	// never block eval.
	[eval] (s22!=1) & (s22!=3) -> true;
  [report] (s22=4) -> (s22'=2);
  [report] (s22!=4) -> true;
	// if the node is infected, then it tries to attack its neighbouring nodes
	[attack32_22] (s22=2) -> true;
	[attack23_22] (s22=2) -> true;
	[attack12_22] (s22=2) -> true;
	[attack21_22] (s22=2) -> true;

endmodule

module n32=n21[s21=s32,detect21=detect32,attack31_21=attack33_32,attack22_21=attack22_32,attack11_21=attack31_32,attack21_31=attack32_33,attack21_22=attack32_22,attack21_11=attack32_31] endmodule

// columns 3..N-1

// column N
module n13=n11[s11=s13,detect11=detect13,attack21_11=attack23_13,attack12_11=attack12_13,attack11_21=attack13_23,attack11_12=attack13_12] endmodule
module n23=n21[s21=s23,detect21=detect23,attack31_21=attack33_23,attack22_21=attack22_23,attack11_21=attack13_23,attack21_31=attack23_33,attack21_22=attack23_22,attack21_11=attack23_13] endmodule

module n33

	s33 : [0..4] init 2; // node infected;
	// 0 - node uninfected
	// 1 - node uninfected but firewall breached
	// 2 - node infected

	// firewall attacked (from an infected neighbour)
	[attack33_32] (s33=0) ->  detect33 : true + (1-detect33) : (s33'=1);
	[attack33_23] (s33=0) ->  detect33 : true + (1-detect33) : (s33'=1);
	// if the firewall has been breached tries to infect the node
	[eval] (s33=1) -> infect : (s33'=4) + (1-infect) : (s33'=3);
	// restore save mode
	[eval] (s33=3) -> (s33'=0);
	// never block eval.
	[eval] (s33!=1) & (s33!=3) -> true;
  [report] (s33=4) -> (s33'=2);
  [report] (s33!=4) -> true;
	// if the node is infected, then it tries to attack its neighbouring nodes
	[attack32_33] (s33=2) -> true;
	[attack23_33] (s33=2) -> true;

endmodule

// reward structure (number of attacks)
rewards "attacks"

	// corner nodes

	[attack11_12] true : 1;
	[attack11_21] true : 1;
	[attack31_21] true : 1;
	[attack31_32] true : 1;
	[attack13_12] true : 1;
	[attack13_23] true : 1;
	[attack33_32] true : 1;
	[attack33_23] true : 1;

	// edge nodes

	[attack12_13] true : 1;
	[attack12_11] true : 1;
	[attack12_22] true : 1;
	[attack21_31] true : 1;
	[attack21_11] true : 1;
	[attack21_22] true : 1;
	[attack32_33] true : 1;
	[attack32_31] true : 1;
	[attack32_22] true : 1;
	[attack23_33] true : 1;
	[attack23_13] true : 1;
	[attack23_22] true : 1;

	// middle nodes

	[attack22_32] true : 1;
	[attack22_23] true : 1;
	[attack22_12] true : 1;
	[attack22_21] true : 1;

endrewards
