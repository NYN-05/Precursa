Precursa v2.0 is your idea for a smart system that automatically fixes problems in shipping cargo across oceans, like when ports get blocked or bad weather hits. It's built for hackathons and uses AI to watch shipments and reroute them without humans clicking buttons.

The Problem
Shipping companies lose billions every year because disruptions—like port congestion, storms, or ship breakdowns—aren't spotted fast enough. Imagine a truck full of medicine (pharma cargo) heading from Mumbai to Europe: a sudden storm or blocked port like Singapore delays it by days, spoiling the medicine or missing deadlines. Humans check alerts manually, taking 4-6 hours to react, but by then, it's too late—costs skyrocket, customers get angry, and money is lost.

Simple Example: Like in 2021, the Ever Given ship got stuck in the Suez Canal. It blocked global trade for days, delaying thousands of shipments. Companies reacted hours later, but your system could have flagged it 18 minutes early using ship position data.

The Solution
Precursa runs an AI "agent" every 2 minutes that checks every shipment's risk score (called DRI, from 0-100). If risk is high (like 75+), it automatically finds new safe routes using math solvers, reroutes the cargo, and explains why in simple words. No human needed—the system heals itself. It shows everything on a map dashboard with live updates, and you can test it with "war games" where one AI creates chaos and another fights it back.

Simple Example: For that pharma truck in a storm—system spots rising risk from weather data, skips the hot port (to keep medicine cold), picks a cooler route via Colombo, saves the cargo, and says: "Rerouted because port congestion added 34% risk and weather 23%—new path cuts delay by 12 hours."

Key Parts in Simple Terms
Risk Checker (ML Ensemble): Three AI models scan data like weather, ship speed, port crowds—give DRI score with "why" (SHAP explains top reasons).

Smart Router: Finds paths but enforces rules—no hot ports for cold cargo, no heavy loads on weak routes.

Auto Agent: LangGraph AI decides and acts alone, logs everything for proof.

Explainer Copilot: Chatbot tells story using only real data, no guesses.

Fun Demo: War game simulates attacks (fake storms), shows money saved live.

In short, Precursa turns chaotic shipping into a self-fixing machine—perfect for your student tech club hackathon wins, spotting issues early and proving it with real history like Ever Given.