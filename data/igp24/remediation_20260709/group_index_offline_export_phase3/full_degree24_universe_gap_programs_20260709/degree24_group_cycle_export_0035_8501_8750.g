
LoadPackage("transgrp");
SizeScreen([1000000, 1000000]);
Print("[\n");
first := true;
for t in [8501,8502,8503,8504,8505,8506,8507,8508,8509,8510,8511,8512,8513,8514,8515,8516,8517,8518,8519,8520,8521,8522,8523,8524,8525,8526,8527,8528,8529,8530,8531,8532,8533,8534,8535,8536,8537,8538,8539,8540,8541,8542,8543,8544,8545,8546,8547,8548,8549,8550,8551,8552,8553,8554,8555,8556,8557,8558,8559,8560,8561,8562,8563,8564,8565,8566,8567,8568,8569,8570,8571,8572,8573,8574,8575,8576,8577,8578,8579,8580,8581,8582,8583,8584,8585,8586,8587,8588,8589,8590,8591,8592,8593,8594,8595,8596,8597,8598,8599,8600,8601,8602,8603,8604,8605,8606,8607,8608,8609,8610,8611,8612,8613,8614,8615,8616,8617,8618,8619,8620,8621,8622,8623,8624,8625,8626,8627,8628,8629,8630,8631,8632,8633,8634,8635,8636,8637,8638,8639,8640,8641,8642,8643,8644,8645,8646,8647,8648,8649,8650,8651,8652,8653,8654,8655,8656,8657,8658,8659,8660,8661,8662,8663,8664,8665,8666,8667,8668,8669,8670,8671,8672,8673,8674,8675,8676,8677,8678,8679,8680,8681,8682,8683,8684,8685,8686,8687,8688,8689,8690,8691,8692,8693,8694,8695,8696,8697,8698,8699,8700,8701,8702,8703,8704,8705,8706,8707,8708,8709,8710,8711,8712,8713,8714,8715,8716,8717,8718,8719,8720,8721,8722,8723,8724,8725,8726,8727,8728,8729,8730,8731,8732,8733,8734,8735,8736,8737,8738,8739,8740,8741,8742,8743,8744,8745,8746,8747,8748,8749,8750] do
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
