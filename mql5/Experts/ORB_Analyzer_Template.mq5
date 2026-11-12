//+------------------------------------------------------------------+
//| ORB_Analyzer_Template.mq5                                        |
//| Read-only template: computes 5m opening range levels (no orders)  |
//| Place in mql5/Experts; compile/test only in demo environment.    |
//+------------------------------------------------------------------+
#property strict

input int  InpOpeningMinutes = 5;     // Opening range minutes
input int  InpATRPeriod      = 14;    // ATR period (daily)
input double InpATRStopFrac  = 0.10;  // SL fraction of ATR (0.10 = 10%)

// NOTE: This is a scaffold template. It does NOT place, modify, or close orders.
// Any execution must go through external Risk/confirmation flow per project policy.

int OnInit()
{
   Print("ORB_Analyzer_Template initialized (read-only). No trading actions.");
   return(INIT_SUCCEEDED);
}

void OnTick()
{
   // Placeholder: in P3/P4 wire data collection and expose OR/ATR/RV via outputs or files.
   // Do not implement OrderSend or trade management here without approved gates.
}
