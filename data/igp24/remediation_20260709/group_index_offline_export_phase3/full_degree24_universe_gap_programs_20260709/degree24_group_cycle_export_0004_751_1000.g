
LoadPackage("transgrp");
SizeScreen([1000000, 1000000]);
Print("[\n");
first := true;
for t in [751,752,753,754,755,756,757,758,759,760,761,762,763,764,765,766,767,768,769,770,771,772,773,774,775,776,777,778,779,780,781,782,783,784,785,786,787,788,789,790,791,792,793,794,795,796,797,798,799,800,801,802,803,804,805,806,807,808,809,810,811,812,813,814,815,816,817,818,819,820,821,822,823,824,825,826,827,828,829,830,831,832,833,834,835,836,837,838,839,840,841,842,843,844,845,846,847,848,849,850,851,852,853,854,855,856,857,858,859,860,861,862,863,864,865,866,867,868,869,870,871,872,873,874,875,876,877,878,879,880,881,882,883,884,885,886,887,888,889,890,891,892,893,894,895,896,897,898,899,900,901,902,903,904,905,906,907,908,909,910,911,912,913,914,915,916,917,918,919,920,921,922,923,924,925,926,927,928,929,930,931,932,933,934,935,936,937,938,939,940,941,942,943,944,945,946,947,948,949,950,951,952,953,954,955,956,957,958,959,960,961,962,963,964,965,966,967,968,969,970,971,972,973,974,975,976,977,978,979,980,981,982,983,984,985,986,987,988,989,990,991,992,993,994,995,996,997,998,999,1000] do
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
