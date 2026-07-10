
LoadPackage("transgrp");
SizeScreen([1000000, 1000000]);
Print("[\n");
first := true;
for t in [7251,7252,7253,7254,7255,7256,7257,7258,7259,7260,7261,7262,7263,7264,7265,7266,7267,7268,7269,7270,7271,7272,7273,7274,7275,7276,7277,7278,7279,7280,7281,7282,7283,7284,7285,7286,7287,7288,7289,7290,7291,7292,7293,7294,7295,7296,7297,7298,7299,7300,7301,7302,7303,7304,7305,7306,7307,7308,7309,7310,7311,7312,7313,7314,7315,7316,7317,7318,7319,7320,7321,7322,7323,7324,7325,7326,7327,7328,7329,7330,7331,7332,7333,7334,7335,7336,7337,7338,7339,7340,7341,7342,7343,7344,7345,7346,7347,7348,7349,7350,7351,7352,7353,7354,7355,7356,7357,7358,7359,7360,7361,7362,7363,7364,7365,7366,7367,7368,7369,7370,7371,7372,7373,7374,7375,7376,7377,7378,7379,7380,7381,7382,7383,7384,7385,7386,7387,7388,7389,7390,7391,7392,7393,7394,7395,7396,7397,7398,7399,7400,7401,7402,7403,7404,7405,7406,7407,7408,7409,7410,7411,7412,7413,7414,7415,7416,7417,7418,7419,7420,7421,7422,7423,7424,7425,7426,7427,7428,7429,7430,7431,7432,7433,7434,7435,7436,7437,7438,7439,7440,7441,7442,7443,7444,7445,7446,7447,7448,7449,7450,7451,7452,7453,7454,7455,7456,7457,7458,7459,7460,7461,7462,7463,7464,7465,7466,7467,7468,7469,7470,7471,7472,7473,7474,7475,7476,7477,7478,7479,7480,7481,7482,7483,7484,7485,7486,7487,7488,7489,7490,7491,7492,7493,7494,7495,7496,7497,7498,7499,7500] do
  label := Concatenation("24T", String(t));
  g := TransitiveGroup(24, t);
  classes := ConjugacyClasses(g);
  cycles := [];
  all_even := true;
  block_sizes := [];
  if not IsPrimitive(g) then
    for b in AllBlocks(g) do
      if Length(b) > 1 and Length(b) < 24 and 24 mod Length(b) = 0 then
        AddSet(block_sizes, Length(b));
      fi;
    od;
  fi;
  for c in classes do
    rep := Representative(c);
    lengths := SortedList(CycleLengths(rep, [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]));
    cycle_text := "";
    for i in [1..Length(lengths)] do
      if i > 1 then
        Append(cycle_text, ".");
      fi;
      Append(cycle_text, String(lengths[i]));
    od;
    AddSet(cycles, cycle_text);
    if SignPerm(rep) = -1 then
      all_even := false;
    fi;
  od;
  if not first then
    Print(",\n");
  fi;
  first := false;
  Print("{\"label\":\"", label, "\",\"t\":", t, ",\"degree\":24,");
  Print("\"group_order\":\"", String(Size(g)), "\",");
  Print("\"primitive\":", IsPrimitive(g), ",");
  Print("\"solvable\":", IsSolvableGroup(g), ",");
  if all_even then
    Print("\"parity\":\"even\",");
  else
    Print("\"parity\":\"mixed\",");
  fi;
  Print("\"status\":\"complete\",\"block_sizes\":[");
  for i in [1..Length(block_sizes)] do
    if i > 1 then
      Print(",\n");
    fi;
    Print(block_sizes[i]);
  od;
  Print("],\"cycle_types\":[\n");
  for i in [1..Length(cycles)] do
    if i > 1 then
      Print(",\n");
    fi;
    Print("\"", cycles[i], "\"");
  od;
  Print("\n]}");
od;
Print("\n]\n");
QUIT;
