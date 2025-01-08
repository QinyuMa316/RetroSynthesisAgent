# Carefully analyze the provided text, using images as a supplementary reference. If there is a conflict between the image and text, prioritize the information from the text.
# Ensure that the extracted reactions are interconnected: each subsequent reaction's reactants must include at least one product from the previous reaction. Continue this sequence until all reactants in the first reaction are common laboratory or commercially available substances.

# reaction_prompt = """
# Extract all distinct chemical reactions mentioned within. Include each reaction only once, if it appears more than once.
# Only extract reactions where all reactants and products are fully identified. Exclude any reaction if any reactant or product is unspecified.
# Ensure that there are no identical substances among the reactants, products, catalysts, and solvents. If any identical substances are found, reconsider the validity of the reaction.
#
# Ensure to unify the substance name throughout.
# Be meticulous not to alter the chemical names in a way that changes the identity of the substances.
# Unify Nomenclature: For example, if you encounter "poly(4-acetylstyrene)" and "poly(4-acetyl styrene)" in the text, recognize that they refer to the same substance. Always use the unified name, "poly(4-acetylstyrene)," in your output.
# Similarly, unify "poly(4-vinylphenol)," "poly(4-hydroxystyrene)," and "Polyvinylphenol" to a single name like "Polyhydroxystyrene."
#
# Format the output strictly as follows:
#
# Reaction 001:
# Reactants: List the IUPAC nomenclatures, separated by commas.
# Products: List the IUPAC nomenclatures, separated by commas.
# Conditions: List the following in the exact order, separated by commas, skip any condition that is not provided or if it is unknown::
# - If a synthesis method is provided, provide a professional term used to describe the reaction
# - If a catalyst is provided, prefix with 'Catalyst: ' followed by the IUPAC nomenclatures.
# - If a solvent is provided, prefix with 'Solvent: ' followed by the IUPAC nomenclatures.
# - If an atmosphere is provided, prefix with 'Atmosphere: ' followed by the specified gas.
# - For temperature, provide specific value or range with °C without any prefix.
# - For pressure, provide specific value or range with atm or bar without any prefix.
# - For duration, provide specific value or range with h or min or d without any prefix.
# - For yield, provide specific value or range in % without any prefix.
#
# Do not include any explanatory notes, brackets, or additional information.
# """
#
#
# How can common laboratory and commercial chemical compounds be used to synthesize "{substance}" in one or more steps? Please provide all reactions based on the given content.
#
# - Confirm that the extracted reactions are interconnected: the reactants in each subsequent reaction must include at least one product from the previous reaction.
#
#
# reaction_prompt_v4 = """
# How can common laboratory and commercial chemical compounds be used to synthesize "{substance}" in one or more steps? Please provide all reactions based on the given content.
#
# You must strictly adhere to the following rules:
# - Note that the given content contains multiple synthesis reactions for "{substance}". Ensure that all reactions are extracted without omission.
# - Confirm that the extracted reactions are interconnected: the reactants in each subsequent reaction must include at least one product from the previous reaction.
# - All names must strictly match the provided content without modification or interpretation. Maintain consistent naming of the substance throughout.
# - Do not use general terms such as "Diamine" or "Dianhydride" to represent a class of substances;
# - Do not use abbreviations for any substance names;
# - Do not include any explanatory notes, brackets, or additional information.
# - All names must be provided in their full specific forms.
# - Be careful to ensure that solvents, catalysts, or other reaction conditions are not mistakenly listed as reactants. Reactants must only include compounds directly involved in the chemical transformation.
#
# Format the output strictly as follows:
#
# Initial Output:
#
# Reaction 001:
# Reactants: List the substances with specific names, separated by commas.
# Products: List the substances with specific names, separated by commas.
# Conditions: List the following in the exact order, separated by commas, skipping any condition that is not provided or is unknown:
# - If a catalyst is provided, prefix with "Catalyst: " followed by the substances with specific names.
# - If a solvent is provided, prefix with "Solvent: " followed by the substances with specific names.
# - If other non-reactive reagents are provided, such as drying agents, stabilizers, adsorbents, buffers, etc., prefix with their respective names (e.g., 'Drying agents: ', 'Stabilizers: ', 'Adsorbents: ', 'Buffers: ') followed by their specific types.
# - If an atmosphere is provided, prefix with "Atmosphere: " followed by the specified gas in full names.
# - For temperature, provide the specific value or range with °C without any prefix.
# - For pressure, provide the specific value or range with atm or bar without any prefix.
# - For duration, provide the specific value or range with h, min, or d without any prefix.
# - For yield, provide the specific value or range in % without any prefix.
#
# Check whether any substance in the Reactants is commonly used as a solvent, catalyst, drying agent, stabilizer, adsorbent, buffer, etc. , move it to the conditions section
# Check whether any general terms such as "Diamine" or "Dianhydride" are identified, recheck the content and modify it.
# Document your checking process. Finally, re-output all the corrected reactions.
#
# Checking process:
# - Reaction 001:
#
# Final Output:
# """


prompt_reaction_extraction_cot = """
Extract all distinct chemical reactions from given content. Include each reaction only once, if it appears more than once.
Only extract reactions where all reactants and products are fully identified. Exclude any reaction if any reactant or product is unspecified.

You must strictly adhere to the following rules:
Confirm that the extracted reactions are interconnected: the reactants in each subsequent reaction must include at least one product from the previous reaction.
Be careful to ensure that solvents, catalysts, or other reaction conditions are not mistakenly listed as reactants. Reactants must only include compounds directly involved in the chemical transformation.
All names must be provided in their full specific forms:
- Maintain consistent naming of each substance throughout.
- Do not use general terms, such as "Diamine" or "Dianhydride," to represent a class of substances for any reactant substance name.
- Do not use abbreviations for any substance name.
- Do not include explanatory notes, brackets, or additional information.

Format the output strictly as follows:

Initial Output:

Reaction 001:
Reactants: List the substances with specific names, separated by commas.
Products: List the substances with specific names, separated by commas.
Conditions: List the following in the exact order, separated by commas, skipping any condition that is not provided or is unknown:
- If a catalyst is provided, prefix with "Catalyst: " followed by the substances with specific names.
- If a solvent is provided, prefix with "Solvent: " followed by the substances with specific names.
- If other non-reactive reagents are provided, such as drying agents, stabilizers, adsorbents, buffers, etc., prefix with their respective names (e.g., 'Drying agents: ', 'Stabilizers: ', 'Adsorbents: ', 'Buffers: ') followed by their specific types.
- If an atmosphere is provided, prefix with "Atmosphere: " followed by the specified gas in full names.
- For temperature, provide the specific value or range with °C without any prefix.
- For pressure, provide the specific value or range with atm or bar without any prefix.
- For duration, provide the specific value or range with h, min, or d without any prefix.
- For yield, provide the specific value or range in % without any prefix.

Check whether any substance in the Reactants is commonly used as a solvent, catalyst, drying agent, stabilizer, adsorbent, buffer, etc.  
Document your checking process. If such a substance is identified, move it to the conditions section. Finally, re-output all the corrected reactions.

Checking Process:
- For Reaction 001:

Final Output:

"""


prompt_reaction_extraction = """
Extract all distinct chemical reactions from given content. Include each reaction only once, if it appears more than once.
Only extract reactions where all reactants and products are fully identified. Exclude any reaction if any reactant or product is unspecified.

You must strictly adhere to the following rules:
Confirm that the extracted reactions are interconnected: the reactants in each subsequent reaction must include at least one product from the previous reaction.
Be careful to ensure that solvents, catalysts, or other reaction conditions are not mistakenly listed as reactants. Reactants must only include compounds directly involved in the chemical transformation.
All names must be provided in their full specific forms:
- Maintain consistent naming of each substance throughout.
- Do not use general terms, such as "Diamine" or "Dianhydride," to represent a class of substances for any reactant substance name.
- Do not use abbreviations for any substance name.
- Do not include explanatory notes, brackets, or additional information.

Format the output strictly as follows:

Reaction 001:
Reactants: List the substances with specific names, separated by commas.
Products: List the substances with specific names, separated by commas.
Conditions: List the following in the exact order, separated by commas, skipping any condition that is not provided or is unknown:
- If a catalyst is provided, prefix with "Catalyst: " followed by the substances with specific names.
- If a solvent is provided, prefix with "Solvent: " followed by the substances with specific names.
- If other non-reactive reagents are provided, such as drying agents, stabilizers, adsorbents, buffers, etc., prefix with their respective names (e.g., 'Drying agents: ', 'Stabilizers: ', 'Adsorbents: ', 'Buffers: ') followed by their specific types.
- If an atmosphere is provided, prefix with "Atmosphere: " followed by the specified gas in full names.
- For temperature, provide the specific value or range with °C without any prefix.
- For pressure, provide the specific value or range with atm or bar without any prefix.
- For duration, provide the specific value or range with h, min, or d without any prefix.
- For yield, provide the specific value or range in % without any prefix.
"""


prompt_reaction_evaluation = """
Reactions:
{reactions}

Check whether any substance in the Reactants is commonly used as a solvent, catalyst, drying agent, stabilizer, adsorbent, buffer, etc.  
Document your checking process. If such a substance is identified, move it to the conditions section. Finally, re-output all the corrected reactions. Ensure the number of reactions in the output matches the original.

Format the output strictly as follows:

Checking process:
- Reaction 001: Describe your process for identifying and reassigning any substances to the conditions section.

Final Output:

Reaction 001:
Reactants: List the substances with specific names, separated by commas.
Products: List the substances with specific names, separated by commas.
Conditions: List the following in the exact order, separated by commas, skipping any condition that is not provided or is unknown:
- If a catalyst is provided, prefix with "Catalyst: " followed by the substances with specific names.
- If a solvent is provided, prefix with "Solvent: " followed by the substances with specific names.
- If other non-reactive reagents are provided, such as drying agents, stabilizers, adsorbents, buffers, etc., prefix with their respective names (e.g., 'Drying agents: ', 'Stabilizers: ', 'Adsorbents: ', 'Buffers: ') followed by their specific types.
- If an atmosphere is provided, prefix with "Atmosphere: " followed by the specified gas in full names.
- For temperature, provide the specific value or range with °C without any prefix.
- For pressure, provide the specific value or range with atm or bar without any prefix.
- For duration, provide the specific value or range with h, min, or d without any prefix.
- For yield, provide the specific value or range in % without any prefix.

"""

prompt_align_root_node = """
For the given reactions, check if any substances are different names for the same entity as "{substance}". If so, standardize all names to "{substance}". 
Ensure that the output includes all original reactions, with only the inconsistent names modified. 
Output the same number of reactions as provided, maintaining the original format. No additional notes, brackets, or information should be included.

reactions:

{reactions}
"""

prompt_template_entity_alignment = """
Substances:
{substances}

Analyze the listed substances and determine if any are identical (completely the same substance, not isomers) but are referred to by different names. If identical substances are found, standardize their names to the most commonly used and scientifically accepted name.
Be meticulous in identifying identical substances and standardizing their names to avoid any omissions.

Provide your output in the following format:

Different names for the same substance:
List all names that refer to the same substance.

Standardized name:
Provide the most commonly used name as the standardized version.

Example Output:

Different names for the same substance: Benzophenonetetracarboxylic dianhydride, Benzophenone tetracarboxylic dianhydride
Standardized name: Benzophenone tetracarboxylic dianhydride

Different names for the same substance: 2,2-bis(3',4'-dicarboxyphenyl)hexafluoropropane dianhydride, 2,2-bis(3,4-dicarboxyphenyl)hexafluoropropane dianhydride
Standardized name: 2,2-bis(3,4-dicarboxyphenyl)hexafluoropropane dianhydride

Different names for the same substance:  4,4′-(hexafluoro-isopropylidene) diphthalic anhydride, hexafluoroisopropylidene diphthalic anhydride
Standardized name: hexafluoroisopropylidene diphthalic anhydride
"""


prompt_add_reactions_from_literature = """
Please answer the questions based on the given content.
How to use common laboratory and commercial chemical compounds to synthesize "{material}" in one or more steps? Please provide the reactions.

Ensure that the extracted reactions are interconnected: each subsequent reaction's reactants must include at least one product from the previous reaction. Continue this sequence until all reactants in the first reaction are common laboratory or commercially available substances.
Ensure to unify the substance name throughout. Be meticulous not to alter the chemical names in a way that changes the identity of the substances.

Format the output strictly as follows:

Reaction 001:
Reactants: List the IUPAC nomenclatures, separated by commas.
Products: List the IUPAC nomenclatures, separated by commas.
Conditions: List the following in the exact order, separated by commas, skip any condition that is not provided or if it is unknown::
- If a synthesis method is provided, provide a professional term used to describe the reaction
- If a catalyst is provided, prefix with 'Catalyst: ' followed by the IUPAC nomenclatures.
- If a solvent is provided, prefix with 'Solvent: ' followed by the IUPAC nomenclatures.
- If other non-reactive reagents are provided, such as drying agents, stabilizers, adsorbents, buffers, etc., prefix with their respective names (e.g., 'Drying agents: ', 'Stabilizers: ', 'Adsorbents: ', 'Buffers: ') followed by their specific types.
- If an atmosphere is provided, prefix with 'Atmosphere: ' followed by the specified gas.
- For temperature, provide specific value or range with °C without any prefix.
- For pressure, provide specific value or range with atm or bar without any prefix.
- For duration, provide specific value or range with h or min or d without any prefix.
- For yield, provide specific value or range in % without any prefix.

Do not include any explanatory notes, brackets, or additional information.
"""


prompt_add_reactions_from_literature_cot = """
Please answer the questions based on the given content.
How to use common laboratory and commercial chemical compounds to synthesize "{material}" in one or more steps? Please provide the reactions.

You must strictly adhere to the following rules:
Confirm that the extracted reactions are interconnected: the reactants in each subsequent reaction must include at least one product from the previous reaction.
Be careful to ensure that solvents, catalysts, or other reaction conditions are not mistakenly listed as reactants. Reactants must only include compounds directly involved in the chemical transformation.
All names must be provided in their full specific forms:
- Maintain consistent naming of each substance throughout.
- Do not use general terms, such as "Diamine" or "Dianhydride," to represent a class of substances for any reactant substance name.
- Do not use abbreviations for any substance name.
- Do not include explanatory notes, brackets, or additional information.

Format the output strictly as follows:

Initial Output:

Reaction 001:
Reactants: List the substances with specific names, separated by commas.
Products: List the substances with specific names, separated by commas.
Conditions: List the following in the exact order, separated by commas, skipping any condition that is not provided or is unknown:
- If a catalyst is provided, prefix with "Catalyst: " followed by the substances with specific names.
- If a solvent is provided, prefix with "Solvent: " followed by the substances with specific names.
- If other non-reactive reagents are provided, such as drying agents, stabilizers, adsorbents, buffers, etc., prefix with their respective names (e.g., 'Drying agents: ', 'Stabilizers: ', 'Adsorbents: ', 'Buffers: ') followed by their specific types.
- If an atmosphere is provided, prefix with "Atmosphere: " followed by the specified gas in full names.
- For temperature, provide the specific value or range with °C without any prefix.
- For pressure, provide the specific value or range with atm or bar without any prefix.
- For duration, provide the specific value or range with h, min, or d without any prefix.
- For yield, provide the specific value or range in % without any prefix.

Check whether any substance in the Reactants is commonly used as a solvent, catalyst, drying agent, stabilizer, adsorbent, buffer, etc.  
Document your checking process. If such a substance is identified, move it to the conditions section. Finally, re-output all the corrected reactions.

Checking Process:
- For Reaction 001:

Final Output:

"""


prompt_reactions_filtration = """
Reactions:
{reactions}

Given Reactions, please filter them according to these conditions:
1. Exclude reactions that lack any reaction conditions.
2. Exclude reactions with high reaction temperatures > 350 °C.
3. Exclude reactions with high reaction pressure > 2 atm.
4. Exclude reactions involving difficult-to-source catalysts.
5. Exclude reactions involving difficult-to-source solvents
6. Exclude reactions involving toxic substances or those that produce toxic byproducts.

Format the output strictly as follows:

Excluded Reactions:
Reaction idx: [idx], Reason: ...

Remaining Reactions:
Reaction idx: [idx]
"""

prompt_filter_pathway = """
Please evaluate the following reaction pathways one by one to determine their validity. If a pathway is not valid, remove it and explain why.

Reaction Pathways:
{all_pathways}

Format the output strictly as follows:

Excluded Reaction Pathways:
Pathway: List reaction indices in order (e.g., idx4, idx7, idx3)
Reason: Provide a concise explanation for why the pathway is not valid.

Remaining Reaction Pathways:
Pathway: List remaining valid reaction indices in order (e.g., idx4, idx7, idx3)
"""


recommend_prompt_template_general = """
Given the target product "{substance}", 
please analyze and recommend the most optimal reaction pathway by following these structured steps:

1. Pathways Analysis with Advantages and Disadvantages:
Please analyze all pathways listed in "Reaction Pathways" comprehensively without any omissions. 
For each pathway, provide a summary of its key features and evaluate its advantages and disadvantages based on:
- Reaction Mildness: Evaluate if the reaction conditions are mild (i.e., requires low temperature, pressure, or a short reaction duration).
- Reactant Availability and Cost: Consider the accessibility and cost-effectiveness of reactants, solvent, catalyst and atmospheric requirements.
- Yield and Scalability: Assess the yield, and discuss the feasibility of scaling for larger production or synthesis.
- Safety Profile: Analyze any safety concerns, particularly regarding the use of toxic, flammable, or otherwise hazardous substances.

2. Final Recommendation:
After evaluating all pathways, select the most suitable pathway and justify your choice by comparing it with the alternatives. Highlight specific aspects that make it superior in terms of mildness, cost, scalability, or safety.


Reaction Pathways:
{all_pathways}


Response Format:

Analysis:

Pathway: List reaction indices (e.g. idx4, idx7, idx3)
Advantages: 
Disadvantages:

Recommended Reaction Pathway: List reaction indices (e.g. idx4, idx7, idx3).

Step 1:
Reaction idx: Specify the reaction index.
Reactants: List the IUPAC nomenclatures, separated by commas.
Products: List the IUPAC nomenclatures, separated by commas.
Conditions: List conditions in specified order; skip if unknown.
Source: Source literature name.

Repeat for each step in the chosen pathway.

Reasons:
Explain the rationale for selecting this pathway over other alternatives, focusing on its advantages in mildness, cost, scalability, or safety.
"""

recommend_prompt_template_cost = """
Given the target product "{substance}", 
please analyze and recommend the reaction pathway that results in the lowest reactant cost by following these structured steps:

1. Reactant Inventory and Cost Analysis:
For each pathway listed in "Reaction Pathways," list all **initial reactants** (only those substances originally introduced into the reaction system, not intermediate products generated in previous steps), as well as any solvents, catalysts, and atmospheric requirements. Focus solely on identifying these elements without evaluating reaction time, yield, number of steps, or any other factors.
After identifying all elements, analyze the pathways comprehensively without any omissions. Evaluate cost-effectiveness for each pathway based exclusively on the accessibility and cost of initial reactants, solvents, catalysts, and atmospheric requirements.

2. Final Recommendation:
Select the pathway with the lowest overall reactant cost after assessing all options. Justify your choice by comparing it with the alternatives, highlighting specific cost-related factors that make this pathway superior.

Reaction Pathways:
{all_pathways}

Response Format:

Inventory & Analysis:

Pathway: List reaction indices (e.g., idx4, idx7, idx3)
Initial Reactants: List only the substances originally introduced, with IUPAC nomenclatures, separated by commas.
Solvents: List all solvents.
Catalysts: List all catalysts.
Atmospheric Requirements: Specify any atmospheric requirements.
Cost Analysis:

Recommended Reaction Pathway: List reaction indices (e.g., idx4, idx7, idx3).

Step 1:
Reaction idx: Specify the reaction index.
Reactants: List the IUPAC nomenclatures, separated by commas.
Products: List the IUPAC nomenclatures, separated by commas.
Conditions: List conditions in specified order; skip if unknown.
Source: Source literature name.

Repeat for each step in the chosen pathway.

Reasons:
Explain the rationale for selecting this pathway over other alternatives, focusing exclusively on its advantages in terms of reactant cost.
"""
# After listing all temperatures and pressures, analyze each pathway comprehensively to evaluate the mildness of reaction conditions, considering only temperature and pressure.

recommend_prompt_template_condition = """
Given the target product "{substance}", 
please analyze and recommend the reaction pathway that has the mildest reaction conditions by following these structured steps:

1. Comprehensive Condition Inventory and Condition Analysis: 
For each pathway listed in "Reaction Pathways," list all relevant reaction temperatures and pressures without considering any other factors (e.g., reaction time, yield, number of steps, or reactant cost).
After listing all temperatures and pressures, conduct a comprehensive analysis of each pathway to evaluate the mildness of reaction conditions strictly based on the listed temperature and pressure values.

3. Final Recommendation:
Select the pathway with the mildest overall reaction conditions based exclusively on temperature and pressure. Justify your choice by comparing it with the alternatives, highlighting specific temperature- or pressure-related factors that make it superior.

Reaction Pathways:
{all_pathways}

Response Format:

Condition Inventory and Analysis:

Pathway: List reaction indices (e.g., idx4, idx7, idx3)
Temperature: List temperature(s) for each reaction step, in degrees Celsius or Kelvin.
Pressure: List pressure(s) for each reaction step, in atm or relevant units.
Condition Analysis: 

Recommended Reaction Pathway: List reaction indices (e.g., idx4, idx7, idx3).

Step 1:
Reaction idx: Specify the reaction index.
Reactants: List the IUPAC nomenclatures, separated by commas.
Products: List the IUPAC nomenclatures, separated by commas.
Conditions: List conditions in specified order; skip if unknown.
Source: Source literature name.

Repeat for each step in the chosen pathway.

Reasons:
Explain the rationale for selecting this pathway over other alternatives, focusing solely on its advantages in terms of mild temperature and pressure conditions.
"""

recommend_prompt_template_specific_substance = """
Reaction Pathways:
{all_pathways}

Please analyze and recommend the most optimal reaction pathways that includes "{initial_reactant}" as one of the initial reactants.

List all reaction pathways from "Reaction Pathways" that include "{initial_reactant}" as an initial reactant.
After listing all relevant pathways, analyze the reaction conditions comprehensively to determine the optimal pathway, considering factors such as mild temperature and pressure requirements, reaction duration, yield, and accessibility of initial reactants and so on.

Format the output strictly as follows:

Analysis:
Pathway: List reaction indices (e.g., idx4, idx7, idx3)
Condition:

Recommended Reaction Pathway: List reaction indices (e.g., idx4, idx7, idx3).

Reaction idx: Specify the reaction index.
Reactants: List the substances with specific names, separated by commas.
Products: List the substances with specific names, separated by commas.
Conditions: List conditions in specified order; skip if unknown.
Source: Source literature name.

Repeat for each step in the chosen pathway.

Reasons:
Explain the rationale for selecting this pathway over other alternatives.
"""

recommend_prompt_commercial = """
Reaction Pathways:
{all_pathways}

Please analyze and recommend the reaction pathways used to manufacture commercially available Katpon polyimide.

Format the output strictly as follows:

Recommended Reaction Pathway: List reaction indices (e.g., idx4, idx7, idx3).

Reaction idx: Specify the reaction index.
Reactants: List the substances with specific names, separated by commas.
Products: List the substances with specific names, separated by commas.
Conditions: List conditions in specified order; skip if unknown.
Source: Source literature name.

Repeat for each step in the chosen pathway.

Reasons:
Explain the rationale for selecting this pathway over other alternatives.
"""





