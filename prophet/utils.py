# utils.py

from pgmpy.models import BayesianModel
from pgmpy.inference import VariableElimination
from pgmpy.factors.discrete import TabularCPD

from .models import Fixture, Player, TeamForm, HeadToHead, Prediction

class PredictionEngine:
    def __init__(self, fixture_id):
        self.fixture = Fixture.objects.get(pk=fixture_id)
        self.home_team = self.fixture.home_team
        self.away_team = self.fixture.away_team
        self.model = self.build_model()

    def build_model(self):
        model = BayesianModel([
            ('HomeForm', 'MatchResult'),
            ('AwayForm', 'MatchResult'),
            ('HomeInjuries', 'MatchResult'),
            ('AwayInjuries', 'MatchResult'),
            ('H2HResult', 'MatchResult'),
            ('ExternalPrediction', 'MatchResult'),
            # for over/under
            ('HomeForm', 'OverUnderResult'),
            ('AwayForm', 'OverUnderResult'),
            ('H2HResult', 'OverUnderResult'),
            # for GG
            ('HomeForm', 'GGResult'),
            ('AwayForm', 'GGResult'),
            ('H2HResult', 'GGResult'),
            # for handicap
            ('HomeForm', 'HandicapResult'),
            ('AwayForm', 'HandicapResult'),
        ])

        # Example CPDs (can be expanded based on data)
        cpd_homeform = TabularCPD(variable='HomeForm', variable_card=2, values=[[0.7], [0.3]])
        cpd_awayform = TabularCPD(variable='AwayForm', variable_card=2, values=[[0.4], [0.6]])
        cpd_homeinj = TabularCPD(variable='HomeInjuries', variable_card=2, values=[[0.9], [0.1]])
        cpd_awayinj = TabularCPD(variable='AwayInjuries', variable_card=2, values=[[0.8], [0.2]])
        cpd_h2h = TabularCPD(variable='H2HResult', variable_card=2, values=[[0.6], [0.4]])
        cpd_extpred = TabularCPD(variable='ExternalPrediction', variable_card=3, values=[[0.5], [0.3], [0.2]])

        # MatchResult
        cpd_matchresult = TabularCPD(variable='MatchResult', variable_card=3,
                                     values=[[0.5], [0.3], [0.2]],
                                     evidence=['HomeForm', 'AwayForm', 'HomeInjuries', 'AwayInjuries', 'H2HResult', 'ExternalPrediction'],
                                     evidence_card=[2,2,2,2,2,3])

        # OverUnderResult
        cpd_ou = TabularCPD(variable='OverUnderResult', variable_card=2,
                            values=[[0.6], [0.4]],
                            evidence=['HomeForm', 'AwayForm', 'H2HResult'],
                            evidence_card=[2,2,2])

        # GGResult
        cpd_gg = TabularCPD(variable='GGResult', variable_card=2,
                            values=[[0.55], [0.45]],
                            evidence=['HomeForm', 'AwayForm', 'H2HResult'],
                            evidence_card=[2,2,2])

        # HandicapResult
        cpd_handicap = TabularCPD(variable='HandicapResult', variable_card=3,
                                  values=[[0.4], [0.3], [0.3]],
                                  evidence=['HomeForm', 'AwayForm'],
                                  evidence_card=[2,2])

        model.add_cpds(cpd_homeform, cpd_awayform, cpd_homeinj, cpd_awayinj, cpd_h2h, cpd_extpred,
                       cpd_matchresult, cpd_ou, cpd_gg, cpd_handicap)

        model.check_model()
        return model

    def get_evidence(self):
        return {
            'HomeForm': self.calculate_form(self.home_team),
            'AwayForm': self.calculate_form(self.away_team),
            'HomeInjuries': self.calculate_injuries(self.home_team),
            'AwayInjuries': self.calculate_injuries(self.away_team),
            'H2HResult': self.calculate_h2h(),
            'ExternalPrediction': self.calculate_external_pred()
        }

    def calculate_form(self, team):
        forms = team.forms.filter(fixture__date__lt=self.fixture.date).order_by('-game_number')[:5]
        wins = forms.filter(result='W').count()
        return 0 if wins >= 3 else 1  # 0=good, 1=bad

    def calculate_injuries(self, team):
        critical = Player.objects.filter(team=team, injury__isnull=False, effect__in=['threat', 'best', 'required'])
        return 0 if not critical.exists() else 1

    def calculate_h2h(self):
        h2h = self.fixture.head_to_heads.order_by('-match_date')[:5]
        home_wins = [h for h in h2h if h.result.split('-')[0] > h.result.split('-')[1]]
        return 0 if len(home_wins) >= 3 else 1

    def calculate_external_pred(self):
        preds = self.fixture.predictions.filter(prediction_type__name='1X2')
        if not preds.exists():
            return 0
        best = max(preds, key=lambda p: p.site_accuracy)
        return {'1': 0, 'X': 1, '2': 2}.get(best.value, 0)

    def predict_1x2(self):
        infer = VariableElimination(self.model)
        result = infer.map_query(['MatchResult'], evidence=self.get_evidence())
        return {0: '1', 1: 'X', 2: '2'}[result['MatchResult']]

    def predict_over_under(self):
        infer = VariableElimination(self.model)
        result = infer.map_query(['OverUnderResult'], evidence=self.get_evidence())
        return {0: 'Over', 1: 'Under'}[result['OverUnderResult']]

    def predict_gg(self):
        infer = VariableElimination(self.model)
        result = infer.map_query(['GGResult'], evidence=self.get_evidence())
        return {0: 'GG', 1: 'No GG'}[result['GGResult']]

    def predict_handicap(self):
        infer = VariableElimination(self.model)
        result = infer.map_query(['HandicapResult'], evidence=self.get_evidence())
        return {0: 'Home Handicap Win', 1: 'Draw Handicap', 2: 'Away Handicap Win'}[result['HandicapResult']]

    def predict_correct_score(self):
        # Dummy → can integrate ML or rule-based later
        return "2-1"
