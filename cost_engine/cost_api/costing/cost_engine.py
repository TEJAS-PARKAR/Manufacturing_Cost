"""
Cost engine orchestrator module.
Coordinates all individual costing modules to calculate total cost.
"""

import logging
from cost_api.database.loaders import RateDatabase
from cost_api.costing.material_cost import MaterialCostCalculator
from cost_api.costing.conversion_cost import ConversionCostCalculator
from cost_api.costing.coating_cost import CoatingCostCalculator
from cost_api.costing.overhead_cost import OverheadCostCalculator
from cost_api.costing.profit_cost import ProfitCostCalculator
from cost_api.models.request_models import CostEstimationRequest
from cost_api.models.response_models import CostEstimationResponse, CostBreakdown
from cost_api.utils.area_calculator import AreaCalculator
from cost_api.utils.weight_calculator import WeightCalculator
from cost_api.utils.validators import InputValidator

logger = logging.getLogger(__name__)


class CostEngine:
    """
    The central orchestrator of the Manufacturing Cost Engine.
    """

    def __init__(self, db: RateDatabase):
        self.db = db
        self.validator = InputValidator(
            known_materials=set(db.material_rates.keys()),
            known_processes=set(db.process_rates.keys()),
            known_coatings=set(db.coating_rates.keys()),
        )
        self.material_calc = MaterialCostCalculator(db.material_rates)
        self.conversion_calc = ConversionCostCalculator(db.process_rates)
        self.coating_calc = CoatingCostCalculator(db.coating_rates)
        self.overhead_calc = OverheadCostCalculator()
        self.profit_calc = ProfitCostCalculator()

    def estimate_cost(self, request: CostEstimationRequest) -> CostEstimationResponse:
        logger.info("Starting cost estimation for part: %s", request.part_name)
        notes = []

        # 1. Validate inputs and collect warnings
        notes.extend(self.validator.validate_material(request.material))
        notes.extend(self.validator.validate_operations(request.operations.model_dump()))
        notes.extend(self.validator.validate_coating(request.surface_treatment))

        # 2. Determine finished weight (provided or auto-calculated)
        finished_weight_kg = request.finished_weight_kg
        if finished_weight_kg is None:
            finished_weight_kg = WeightCalculator.calculate_weight_kg(
                length_mm=request.length_mm,
                width_mm=request.width_mm,
                thickness_mm=request.thickness_mm,
                material=request.material,
            )
            notes.append(f"Finished weight auto-calculated: {finished_weight_kg} kg")
            logger.info("Auto-calculated weight: %.4f kg", finished_weight_kg)

        # 3. Determine surface area (provided or auto-calculated)
        area_m2 = request.area_m2
        if area_m2 is None:
            area_m2 = AreaCalculator.calculate_area_m2(
                length_mm=request.length_mm,
                width_mm=request.width_mm,
            )
            notes.append(f"Surface area auto-calculated: {area_m2} m2")
            logger.info("Auto-calculated area: %.9f m2", area_m2)

        # 4. Calculate individual cost components
        # Raw Material Cost
        try:
            rm_cost, rm_warnings = self.material_calc.calculate(
                material=request.material,
                finished_weight_kg=finished_weight_kg,
            )
            notes.extend(rm_warnings)
        except ValueError as e:
            logger.error("Material cost calculation failed: %s", e)
            rm_cost = 0.0
            notes.append(f"Error calculating raw material cost: {str(e)}")

        # Conversion Cost
        conversion_cost, conv_warnings = self.conversion_calc.calculate(
            operations=request.operations.model_dump()
        )
        notes.extend(conv_warnings)

        # Coating Cost
        coating_cost, coat_warnings = self.coating_calc.calculate(
            surface_treatment=request.surface_treatment,
            area_m2=area_m2,
        )
        notes.extend(coat_warnings)

        # Overhead, ICC, and Rejection
        overhead = self.overhead_calc.calculate_overhead(conversion_cost)
        icc = self.overhead_calc.calculate_icc(rm_cost)
        rejection = self.overhead_calc.calculate_rejection(rm_cost, conversion_cost)

        # Profit
        profit = self.profit_calc.calculate(rm_cost, conversion_cost)

        # 5. Sum total cost
        total_cost = (
            rm_cost
            + conversion_cost
            + coating_cost
            + overhead
            + icc
            + rejection
            + profit
        )
        total_cost = round(total_cost, 2)

        # 6. Build response
        breakdown = CostBreakdown(
            raw_material_cost=rm_cost,
            conversion_cost=conversion_cost,
            coating_cost=coating_cost,
            overhead=overhead,
            icc=icc,
            rejection=rejection,
            profit=profit,
            total_cost=total_cost,
        )

        logger.info("Total calculated cost: %.2f INR", total_cost)

        return CostEstimationResponse(
            part_name=request.part_name,
            material=request.material,
            finished_weight_kg=finished_weight_kg,
            area_m2=area_m2,
            cost_breakdown=breakdown,
            notes=notes,
        )
