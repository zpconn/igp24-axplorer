
LoadPackage("transgrp");
SizeScreen([1000000, 1000000]);
Print("[\n");
first := true;
for t in [2501,2502,2503,2504,2505,2506,2507,2508,2509,2510,2511,2512,2513,2514,2515,2516,2517,2518,2519,2520,2521,2522,2523,2524,2525,2526,2527,2528,2529,2530,2531,2532,2533,2534,2535,2536,2537,2538,2539,2540,2541,2542,2543,2544,2545,2546,2547,2548,2549,2550,2551,2552,2553,2554,2555,2556,2557,2558,2559,2560,2561,2562,2563,2564,2565,2566,2567,2568,2569,2570,2571,2572,2573,2574,2575,2576,2577,2578,2579,2580,2581,2582,2583,2584,2585,2586,2587,2588,2589,2590,2591,2592,2593,2594,2595,2596,2597,2598,2599,2600,2601,2602,2603,2604,2605,2606,2607,2608,2609,2610,2611,2612,2613,2614,2615,2616,2617,2618,2619,2620,2621,2622,2623,2624,2625,2626,2627,2628,2629,2630,2631,2632,2633,2634,2635,2636,2637,2638,2639,2640,2641,2642,2643,2644,2645,2646,2647,2648,2649,2650,2651,2652,2653,2654,2655,2656,2657,2658,2659,2660,2661,2662,2663,2664,2665,2666,2667,2668,2669,2670,2671,2672,2673,2674,2675,2676,2677,2678,2679,2680,2681,2682,2683,2684,2685,2686,2687,2688,2689,2690,2691,2692,2693,2694,2695,2696,2697,2698,2699,2700,2701,2702,2703,2704,2705,2706,2707,2708,2709,2710,2711,2712,2713,2714,2715,2716,2717,2718,2719,2720,2721,2722,2723,2724,2725,2726,2727,2728,2729,2730,2731,2732,2733,2734,2735,2736,2737,2738,2739,2740,2741,2742,2743,2744,2745,2746,2747,2748,2749,2750] do
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
