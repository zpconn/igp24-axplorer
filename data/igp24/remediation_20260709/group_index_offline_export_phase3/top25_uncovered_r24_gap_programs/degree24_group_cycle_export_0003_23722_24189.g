
LoadPackage("transgrp");
Print("[\n");
first := true;
for t in [23722,23741,23742,24089,24189] do
  label := Concatenation("24T", String(t));
  g := TransitiveGroup(24, t);
  classes := ConjugacyClasses(g);
  cycles := [];
  all_even := true;
  block_sizes := [];
  if not IsPrimitive(g, [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]) then
    for b in AllBlocks(g, [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]) do
      if Length(b) > 1 and Length(b) < 24 and 24 mod Length(b) = 0 then
        AddSet(block_sizes, Length(b));
      fi;
    od;
  fi;
  for c in classes do
    rep := Representative(c);
    lengths := SortedList(CycleLengthsPerm(rep, [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]));
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
  Print("\"primitive\":", IsPrimitive(g, [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]), ",");
  Print("\"solvable\":", IsSolvableGroup(g), ",");
  if all_even then
    Print("\"parity\":\"even\",");
  else
    Print("\"parity\":\"mixed\",");
  fi;
  Print("\"status\":\"complete\",\"block_sizes\":[");
  for i in [1..Length(block_sizes)] do
    if i > 1 then
      Print(",");
    fi;
    Print(block_sizes[i]);
  od;
  Print("],\"cycle_types\":[");
  for i in [1..Length(cycles)] do
    if i > 1 then
      Print(",");
    fi;
    Print("\"", cycles[i], "\"");
  od;
  Print("]}");
od;
Print("\n]\n");
QUIT;
