import stormpy
import paynt.verification.property
import payntbind

smg_file = "models/smg/example_smg.nm"
prop = "<<circle>> R{\"rew\"}max=? [F \"goal\"]"
# prop = "<<circle>> R{\"rew\"}min=? [F s=2]"
# prop = "<<circle>> Pmax=? [F \"goal\"]"

program = stormpy.parse_prism_program(smg_file)
properties = stormpy.parse_properties_for_prism_program(prop, program, None)
formula = properties[0].raw_formula
model = stormpy.build_model(program, properties)
paynt.verification.property.Property.initialize()

result = payntbind.synthesis.model_check_smg(model, formula,
                                             only_initial_states=False,
                                             set_produce_schedulers=True,
                                             env=paynt.verification.property.Property.environment
)

exit()