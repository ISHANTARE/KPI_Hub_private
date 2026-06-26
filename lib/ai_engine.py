import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── optional scientific imports ──────────────────────────────
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("[AIEngine] numpy not available — statistical features disabled")

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("[AIEngine] scikit-learn not available — ML features disabled")

try:
    from scipy import stats as _scipy_stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


# ============================================================
# TREND ANALYSER
# ============================================================

class TrendAnalyzer:
    """
    Lightweight trend analysis over a list of float values.
    All methods degrade gracefully when numpy/sklearn are absent.
    """

    @staticmethod
    def calculate_trend(
        values: List[float],
        timestamps: Optional[List[datetime]] = None,
    ) -> Dict:
        """
        Fit a linear regression to `values` and return trend metadata.

        Returns
        -------
        dict with keys:
            direction   — 'increasing' | 'decreasing' | 'stable' | 'insufficient_data'
            slope       — regression slope (units per period)
            r_squared   — goodness-of-fit (0–1)
            confidence  — 0–100 score weighted by R² and sample size
            data_points — number of observations
        """
        if len(values) < 3:
            return {
                'direction':   'insufficient_data',
                'slope':       0.0,
                'r_squared':   0.0,
                'confidence':  0.0,
                'data_points': len(values),
            }

        if not NUMPY_AVAILABLE or not SKLEARN_AVAILABLE:
            # Simple fallback: compare first and last thirds
            third  = max(1, len(values) // 3)
            early  = sum(values[:third]) / third
            late   = sum(values[-third:]) / third
            slope  = (late - early) / max(len(values) - third, 1)
            return {
                'direction':   'increasing' if slope > 0.05 else 'decreasing' if slope < -0.05 else 'stable',
                'slope':       round(slope, 4),
                'r_squared':   0.0,
                'confidence':  50.0,
                'data_points': len(values),
            }

        x = np.arange(len(values), dtype=float).reshape(-1, 1)
        y = np.array(values, dtype=float)

        model = LinearRegression()
        model.fit(x, y)
        slope     = float(model.coef_[0])
        r_squared = float(model.score(x, y))

        if abs(slope) < 0.01:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'

        # Confidence rises with R² and sample size, capped at 95
        confidence = min(r_squared * 100 * (1 + len(values) / 30), 95.0)

        return {
            'direction':   direction,
            'slope':       round(slope, 4),
            'r_squared':   round(r_squared, 4),
            'confidence':  round(confidence, 1),
            'data_points': len(values),
        }

    @staticmethod
    def detect_anomalies(
        values: List[float],
        contamination: float = 0.1,
    ) -> List[int]:
        """
        Return indices of anomalous values using Isolation Forest.
        Returns [] when sklearn is unavailable or sample is too small.
        Minimum 10 observations required for meaningful detection.
        """
        if len(values) < 10:
            logger.debug(
                f"[TrendAnalyzer] Anomaly detection skipped — "
                f"only {len(values)} points (min 10)"
            )
            return []

        if not NUMPY_AVAILABLE or not SKLEARN_AVAILABLE:
            logger.debug("[TrendAnalyzer] Anomaly detection skipped — sklearn unavailable")
            return []

        try:
            X           = np.array(values, dtype=float).reshape(-1, 1)
            clf         = IsolationForest(
                contamination=contamination, random_state=42, n_estimators=100
            )
            predictions = clf.fit_predict(X)
            anomaly_idx = [i for i, p in enumerate(predictions) if p == -1]
            logger.debug(
                f"[TrendAnalyzer] Detected {len(anomaly_idx)} anomaly(ies) "
                f"in {len(values)} values"
            )
            return anomaly_idx
        except Exception as exc:
            logger.error(f"[TrendAnalyzer] Anomaly detection error: {exc}")
            return []

    @staticmethod
    def calculate_moving_average(
        values: List[float],
        window: int = 3,
    ) -> List[float]:
        """Return a simple centred moving average over `window` periods."""
        if len(values) < window:
            return list(values)

        if NUMPY_AVAILABLE:
            result = []
            arr = np.array(values, dtype=float)
            for i in range(len(arr)):
                start = max(0, i - window + 1)
                result.append(float(np.mean(arr[start: i + 1])))
            return result

        # Pure-Python fallback
        result = []
        for i in range(len(values)):
            start = max(0, i - window + 1)
            chunk = values[start: i + 1]
            result.append(sum(chunk) / len(chunk))
        return result

    @staticmethod
    def detect_stagnation(
        values: List[float],
        variance_threshold: float = 0.25,
        periods: int = 4,
    ) -> bool:
        """
        Return True when the last `periods` values show near-zero variance,
        indicating the metric is stuck rather than improving.
        """
        if len(values) < periods:
            return False
        recent = values[-periods:]
        if NUMPY_AVAILABLE:
            return float(np.var(recent)) < variance_threshold
        mean   = sum(recent) / len(recent)
        var    = sum((v - mean) ** 2 for v in recent) / len(recent)
        return var < variance_threshold


# ============================================================
# FORECASTER
# ============================================================

class Forecaster:
    """Linear extrapolation with 95% prediction intervals."""

    @staticmethod
    def linear_forecast(values: List[float], periods: int = 7) -> Dict:
        """
        Forecast `periods` steps ahead using OLS linear regression.

        Returns
        -------
        dict with keys:
            forecast     — list of predicted values
            upper_bound  — 95% CI upper
            lower_bound  — 95% CI lower
            confidence   — 0–95 score
            periods      — number of forecast steps
        """
        if len(values) < 3:
            return {
                'forecast':    [],
                'upper_bound': [],
                'lower_bound': [],
                'confidence':  0.0,
                'periods':     periods,
            }

        if not NUMPY_AVAILABLE or not SKLEARN_AVAILABLE:
            # Simple last-value extrapolation
            last  = values[-1]
            delta = (values[-1] - values[0]) / max(len(values) - 1, 1)
            fc    = [round(last + delta * (i + 1), 2) for i in range(periods)]
            return {
                'forecast':    fc,
                'upper_bound': [v + 5 for v in fc],
                'lower_bound': [max(0, v - 5) for v in fc],
                'confidence':  40.0,
                'periods':     periods,
            }

        x = np.arange(len(values), dtype=float).reshape(-1, 1)
        y = np.array(values, dtype=float)

        model = LinearRegression()
        model.fit(x, y)

        future_x    = np.arange(len(values), len(values) + periods, dtype=float).reshape(-1, 1)
        predictions = model.predict(future_x)

        residuals   = y - model.predict(x)
        std_error   = float(np.std(residuals))
        r_squared   = float(model.score(x, y))
        confidence  = round(min(r_squared * 100, 95.0), 1)

        return {
            'forecast':    [round(float(p), 2) for p in predictions],
            'upper_bound': [round(float(p) + 1.96 * std_error, 2) for p in predictions],
            'lower_bound': [round(max(0.0, float(p) - 1.96 * std_error), 2) for p in predictions],
            'confidence':  confidence,
            'periods':     periods,
        }

    @staticmethod
    def forecast_target_achievement(
        current: float,
        target: float,
        historical_velocity: float,   # units improved per period
        remaining_time: int,          # periods remaining
    ) -> Dict:
        """
        Estimate the probability of reaching `target` from `current`
        given `historical_velocity` over `remaining_time` periods.
        """
        gap               = target - current
        required_velocity = gap / remaining_time if remaining_time > 0 else float('inf')

        if historical_velocity <= 0:
            probability = 0.0 if gap > 0 else 100.0
        elif required_velocity <= 0:
            probability = 100.0
        else:
            probability = min((historical_velocity / required_velocity) * 100, 100.0)

        risk = (
            'low'      if probability >= 80 else
            'medium'   if probability >= 60 else
            'high'     if probability >= 40 else
            'critical'
        )

        return {
            'current':             current,
            'target':              target,
            'gap':                 round(gap, 2),
            'required_velocity':   round(required_velocity, 4),
            'historical_velocity': round(historical_velocity, 4),
            'probability':         round(probability, 1),
            'risk':                risk,
            'remaining_time':      remaining_time,
        }


# ============================================================
# RISK ANALYSER
# ============================================================

class RiskAnalyzer:
    """Risk scoring, hotspot detection, and resolution estimation."""

    PROBABILITY_SCORES: Dict[str, int] = {'low': 1, 'medium': 2, 'high': 3}
    IMPACT_SCORES: Dict[str, int]      = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}

    @classmethod
    def calculate_risk_score(
        cls, probability: str, impact: str
    ) -> Tuple[int, str]:
        """
        Return (numeric_score, level_string) from probability × impact.
        Score ranges: 1–2 → low, 3–5 → medium, 6–8 → high, 9–12 → critical.
        """
        p_score = cls.PROBABILITY_SCORES.get((probability or 'medium').lower(), 2)
        i_score = cls.IMPACT_SCORES.get((impact or 'medium').lower(), 2)
        score   = p_score * i_score

        level = (
            'critical' if score >= 9 else
            'high'     if score >= 6 else
            'medium'   if score >= 3 else
            'low'
        )
        return score, level

    @staticmethod
    def identify_risk_hotspots(
        risks: List[Dict],
        components: List[Dict],   # kept for future domain-component correlation
    ) -> List[Dict]:
        """
        Aggregate risk counts per domain and compute a composite hotspot score.
        Domains scoring ≥ 10 are flagged as hotspots.
        """
        hotspots: Dict[str, Dict] = {}

        for risk in risks:
            domain = risk.get('domain', 'Unknown')
            level  = (risk.get('level') or 'low').lower()
            if domain not in hotspots:
                hotspots[domain] = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            hotspots[domain][level] = hotspots[domain].get(level, 0) + 1

        results = []
        for domain, counts in hotspots.items():
            score = (
                counts.get('critical', 0) * 4
                + counts.get('high',     0) * 3
                + counts.get('medium',   0) * 2
                + counts.get('low',      0) * 1
            )
            results.append({
                'domain':     domain,
                'score':      score,
                'counts':     counts,
                'is_hotspot': score >= 10,
            })

        return sorted(results, key=lambda x: x['score'], reverse=True)

    @staticmethod
    def estimate_resolution_time(risk: Dict) -> int:
        """
        Estimate remaining working days to resolve a risk based on its
        level and current mitigation progress.
        """
        default_days = {'critical': 5, 'high': 10, 'medium': 21, 'low': 30}
        level        = (risk.get('level') or 'medium').lower()
        base_days    = default_days.get(level, 21)
        progress     = float(risk.get('mitigation_progress') or 0)
        remaining    = max(0.0, (100.0 - progress) / 100.0)
        return max(1, int(base_days * remaining))


# ============================================================
# RECOMMENDATION ENGINE
# ============================================================

class RecommendationEngine:
    """
    Generates prioritised, actionable recommendations from live data.
    All key references match the normalised to_dict() output in models.py:
        risk:      level, description, domain, mitigation_progress
        component: maturity, risk_level, name, component_id, domain
        ecr:       status, priority, due_date, title, domain
        kpi:       current_value (or current), domain, variance
    """

    _PRIORITY_ORDER = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}

    def generate_recommendations(
        self,
        kpis:       List[Dict],
        components: List[Dict],
        risks:      List[Dict],
        ecrs:       List[Dict],
        actions:    Optional[List[Dict]] = None,
    ) -> List[Dict]:
        recs: List[Dict] = []
        recs.extend(self._analyse_risks(risks))
        recs.extend(self._analyse_components(components))
        recs.extend(self._analyse_ecrs(ecrs))
        recs.extend(self._analyse_kpis(kpis))
        if actions:
            recs.extend(self._analyse_actions(actions))

        recs.sort(key=lambda r: self._PRIORITY_ORDER.get(r.get('priority', 'low'), 4))
        return recs

    # ── risk recommendations ─────────────────────────────────

    def _analyse_risks(self, risks: List[Dict]) -> List[Dict]:
        recs: List[Dict] = []

        critical = [r for r in risks if (r.get('level') or '').lower() == 'critical']
        high     = [r for r in risks if (r.get('level') or '').lower() == 'high']

        if critical:
            ids = ", ".join(
                r.get('id', r.get('risk_id', '?')) for r in critical[:3]
            )
            recs.append({
                'priority':          'critical',
                'title':             f'Address {len(critical)} Critical Risk(s) Immediately',
                'fact':              f'{len(critical)} risks at critical level.',
                'insight':           'Critical risks directly reduce release readiness by 4% each.',
                'action':            (
                    f'Escalate to leadership. Accelerate mitigation for: {ids}. '
                    f'Assign dedicated owners within 24 hours.'
                ),
                'confidence':        95,
                'domain':            critical[0].get('domain') if critical else None,
                'related_entity_type': 'risk',
            })

        if len(high) > 3:
            recs.append({
                'priority':          'high',
                'title':             f'High Risk Concentration: {len(high)} High-Level Risks',
                'fact':              f'{len(high)} high-level risks across domains.',
                'insight':           'Concentration of high risks signals systemic weakness.',
                'action':            (
                    'Schedule a risk review. Prioritise the top 5 by impact score. '
                    'Add to Action Tracking.'
                ),
                'confidence':        88,
                'related_entity_type': 'risk',
            })

        # Stagnant mitigations: progress < 20% on critical/high
        stagnant = [
            r for r in critical + high
            if float(r.get('mitigation_progress') or 0) < 20
        ]
        if stagnant:
            recs.append({
                'priority':          'high',
                'title':             f'{len(stagnant)} Risk(s) with Stalled Mitigation (<20%)',
                'fact':              f'{len(stagnant)} critical/high risks show <20% mitigation progress.',
                'insight':           'Stalled mitigations compound readiness loss over time.',
                'action':            'Review blockers. Re-assign owners. Set 1-week sprint goal.',
                'confidence':        85,
                'related_entity_type': 'risk',
            })

        return recs

    # ── component recommendations ────────────────────────────

    def _analyse_components(self, components: List[Dict]) -> List[Dict]:
        recs: List[Dict] = []

        # Use risk_level (matches models.py to_dict)
        critical_comps = [
            c for c in components
            if (c.get('risk_level') or '').lower() == 'critical'
        ]
        low_maturity = [
            c for c in components
            if (c.get('maturity') or 100) < 60
        ]
        medium_maturity = [
            c for c in components
            if 60 <= (c.get('maturity') or 100) < 75
        ]

        if critical_comps:
            names = ", ".join(
                c.get('name', c.get('id', c.get('component_id', '?')))
                for c in critical_comps[:3]
            )
            recs.append({
                'priority':          'critical',
                'title':             f'{len(critical_comps)} Component(s) at Critical Risk',
                'fact':              f'Critical-risk components: {names}.',
                'insight':           'Critical-risk components block release gate sign-off.',
                'action':            (
                    'Assign senior engineers immediately. '
                    'Consider design alternatives. '
                    'Schedule daily stand-up until resolved.'
                ),
                'confidence':        92,
                'related_entity_type': 'component',
            })

        if low_maturity:
            names = ", ".join(
                c.get('name', c.get('id', c.get('component_id', '?')))
                for c in low_maturity[:3]
            )
            recs.append({
                'priority':          'high',
                'title':             f'{len(low_maturity)} Component(s) Below 60% Maturity',
                'fact':              f'Low-maturity items: {names}.',
                'insight':           'Components under 60% are likely to miss integration milestones.',
                'action':            (
                    'Allocate extra resource. '
                    'Run focused development sprints. '
                    'Set 70% maturity gate within 2 weeks.'
                ),
                'confidence':        85,
                'related_entity_type': 'component',
            })

        if medium_maturity:
            recs.append({
                'priority':          'medium',
                'title':             f'{len(medium_maturity)} Component(s) at 60–75% Maturity',
                'fact':              f'{len(medium_maturity)} components need maturity improvement.',
                'insight':           'These items risk missing the 80% readiness gate.',
                'action':            (
                    'Schedule fortnightly maturity reviews. '
                    'Identify blocking tasks and clear them.'
                ),
                'confidence':        75,
                'related_entity_type': 'component',
            })

        return recs

    # ── ECR recommendations ──────────────────────────────────

    def _analyse_ecrs(self, ecrs: List[Dict]) -> List[Dict]:
        recs: List[Dict] = []
        today   = datetime.utcnow().date()

        pending = [
            e for e in ecrs
            if (e.get('status') or '').lower() in ('pending', 'review')
        ]
        critical_pending = [
            e for e in pending
            if (e.get('priority') or '').lower() == 'critical'
        ]

        # Overdue detection — use due_date (matches models.py)
        overdue: List[Dict] = []
        for e in pending:
            raw_due = e.get('due_date') or e.get('due')
            if raw_due:
                try:
                    due = datetime.strptime(str(raw_due)[:10], '%Y-%m-%d').date()
                    if due < today:
                        overdue.append(e)
                except ValueError:
                    pass

        if overdue:
            recs.append({
                'priority':          'high',
                'title':             f'{len(overdue)} Overdue ECR(s) Require Immediate Action',
                'fact':              f'{len(overdue)} ECRs have passed their due date.',
                'insight':           'Overdue ECRs create cascading schedule delays.',
                'action':            (
                    'Expedite review for all overdue items. '
                    'Escalate to domain leads. '
                    'Update due dates or close as rejected.'
                ),
                'confidence':        92,
                'related_entity_type': 'ecr',
            })

        if len(pending) > 5:
            priority = 'high' if len(pending) > 15 or critical_pending else 'medium'
            recs.append({
                'priority':          priority,
                'title':             f'ECR Backlog: {len(pending)} Pending Requests',
                'fact':              (
                    f'{len(pending)} ECRs pending, '
                    f'including {len(critical_pending)} critical.'
                ),
                'insight':           (
                    f'Backlog costs {len(pending) * 0.5:.1f}% readiness. '
                    'Growing backlogs increase review bottleneck.'
                ),
                'action':            (
                    'Implement priority-queue processing. '
                    'Add reviewer capacity. '
                    'Aim to halve the backlog within 5 business days.'
                ),
                'confidence':        82,
                'related_entity_type': 'ecr',
            })

        return recs

    # ── KPI recommendations ──────────────────────────────────

    def _analyse_kpis(self, kpis: List[Dict]) -> List[Dict]:
        recs: List[Dict] = []

        # Group by domain, use current_value for consistency with models.py
        domain_perf: Dict[str, List[Dict]] = {}
        for kpi in kpis:
            domain = kpi.get('domain', 'Unknown')
            domain_perf.setdefault(domain, []).append(kpi)

        for domain, dkpis in domain_perf.items():
            # Prefer current_value; fall back to current for legacy data
            values = [
                float(k.get('current_value') or k.get('current') or 0)
                for k in dkpis
            ]
            failing = [k for k in dkpis if (k.get('variance') or 0) < 0]

            if not values:
                continue
            avg = sum(values) / len(values)

            if avg < 80 and failing:
                priority = 'high' if avg < 70 else 'medium'
                recs.append({
                    'priority':          priority,
                    'title':             f'{domain} KPI Average Below Target ({avg:.1f}%)',
                    'fact':              (
                        f'{domain}: avg={avg:.1f}% across {len(dkpis)} KPIs, '
                        f'{len(failing)} below target.'
                    ),
                    'insight':           (
                        f'Domain underperformance indicates resource constraints or blockers.'
                    ),
                    'action':            (
                        f'Review {domain} KPI analysis page. '
                        f'Create action items for the {len(failing)} failing KPI(s). '
                        f'Consider resource reallocation.'
                    ),
                    'confidence':        78,
                    'domain':            domain,
                    'related_entity_type': 'kpi',
                })

        return recs

    # ── action recommendations ───────────────────────────────

    def _analyse_actions(self, actions: List[Dict]) -> List[Dict]:
        recs: List[Dict] = []
        today   = datetime.utcnow().date()
        overdue = []

        for a in actions:
            if (a.get('status') or '').lower() == 'closed':
                continue
            raw_due = a.get('due_date')
            if raw_due:
                try:
                    due = datetime.strptime(str(raw_due)[:10], '%Y-%m-%d').date()
                    if due < today:
                        overdue.append(a)
                except ValueError:
                    pass

        if overdue:
            recs.append({
                'priority':          'high',
                'title':             f'{len(overdue)} Overdue Action(s)',
                'fact':              f'{len(overdue)} open actions are past their due date.',
                'insight':           'Overdue actions indicate execution gaps.',
                'action':            (
                    'Contact owners immediately. '
                    'Update due dates or escalate. '
                    'Review in next stand-up.'
                ),
                'confidence':        90,
                'related_entity_type': 'action',
            })

        return recs


# ============================================================
# AI ENGINE  (top-level orchestrator)
# ============================================================

class AIEngine:
    """
    Orchestrates all analytical sub-engines and returns a unified
    analysis payload consumed by /api/ai/analysis and the Insights page.
    """

    def __init__(self):
        self.trend_analyzer         = TrendAnalyzer()
        self.forecaster             = Forecaster()
        self.risk_analyzer          = RiskAnalyzer()
        self.recommendation_engine  = RecommendationEngine()

    # ── domain trend analysis ────────────────────────────────

    def analyze_domain_trends(
        self,
        metrics_history: List[Dict],
        domain: str,
    ) -> Dict:
        """
        Analyse historical metric snapshots for a single domain.
        `metrics_history` items are expected to have `domain` and `value` keys.
        """
        domain_metrics = [
            m for m in metrics_history
            if (m.get('domain') or '') == domain
        ]
        if not domain_metrics:
            return {'domain': domain, 'status': 'no_data', 'data_points': 0}

        # Sort by recorded_at if present
        domain_metrics.sort(key=lambda m: m.get('recorded_at', ''))
        values = [float(m.get('value', 0)) for m in domain_metrics]

        trend      = self.trend_analyzer.calculate_trend(values)
        forecast   = self.forecaster.linear_forecast(values, periods=7)
        anomalies  = self.trend_analyzer.detect_anomalies(values)
        stagnation = self.trend_analyzer.detect_stagnation(values)
        moving_avg = self.trend_analyzer.calculate_moving_average(values)

        return {
            'domain':         domain,
            'current_value':  round(values[-1], 2) if values else 0,
            'avg_value':      round(sum(values) / len(values), 2),
            'trend':          trend,
            'forecast':       forecast,
            'moving_average': [round(v, 2) for v in moving_avg[-7:]],
            'anomaly_count':  len(anomalies),
            'anomaly_indices': anomalies,
            'is_stagnating':  stagnation,
            'data_points':    len(values),
        }

    # ── release readiness ────────────────────────────────────

    def calculate_release_readiness(
        self,
        components: List[Dict],
        domain: str = 'B-Release',
    ) -> Dict:
        """
        Calculate release readiness for a domain.

        Filters components by domain (not phase — phase is Design/Build/Testing).
        Mature = maturity >= 80%.
        """
        domain_comps = [
            c for c in components
            if domain in (c.get('domain') or '')
        ]
        if not domain_comps:
            return {
                'release':    domain,
                'readiness':  0.0,
                'status':     'no_components',
                'total':      0,
                'mature':     0,
                'at_risk':    0,
            }

        total    = len(domain_comps)
        mature   = sum(1 for c in domain_comps if (c.get('maturity') or 0) >= 80)
        at_risk  = sum(
            1 for c in domain_comps
            if (c.get('risk_level') or '').lower() in ('high', 'critical')
        )
        readiness = round((mature / total) * 100, 1) if total else 0.0

        status = (
            'ready'    if readiness >= 90 and at_risk == 0 else
            'on_track' if readiness >= 75 else
            'at_risk'  if readiness >= 50 else
            'critical'
        )

        return {
            'release':             domain,
            'total_components':    total,
            'mature_components':   mature,
            'at_risk_components':  at_risk,
            'readiness':           readiness,
            'status':              status,
        }

    # ── full analysis ────────────────────────────────────────

    def get_full_analysis(
        self,
        kpis:            List[Dict],
        components:      List[Dict],
        risks:           List[Dict],
        ecrs:            List[Dict],
        actions:         Optional[List[Dict]] = None,
        metrics_history: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Return a comprehensive analysis dict ready for the Insights page.
        Domains are derived from actual data — nothing is hardcoded.
        """
        actions = actions or []

        # ── derive domains from live data ────────────────────
        all_domains = sorted({
            c.get('domain', '') for c in components
            if c.get('domain')
        })
        if not all_domains:
            all_domains = ['B-Release', 'K-Release', 'Quality']

        # ── domain trend analysis ────────────────────────────
        domain_analysis: Dict[str, Any] = {}
        for domain in all_domains:
            if metrics_history:
                domain_analysis[domain] = self.analyze_domain_trends(
                    metrics_history, domain
                )
            else:
                # Fallback: compute from current component maturities
                dc     = [c for c in components if domain in (c.get('domain') or '')]
                values = [float(c.get('maturity', 0)) for c in dc]
                avg    = round(sum(values) / len(values), 1) if values else 0.0
                domain_analysis[domain] = {
                    'domain':        domain,
                    'current_value': avg,
                    'kpi_count':     len([k for k in kpis if k.get('domain') == domain]),
                    'component_count': len(dc),
                    'status':        'live_snapshot',
                }

        # ── release readiness per domain ─────────────────────
        release_readiness = {
            domain: self.calculate_release_readiness(components, domain)
            for domain in all_domains
        }

        # ── risk hotspots ────────────────────────────────────
        hotspots = self.risk_analyzer.identify_risk_hotspots(risks, components)

        # ── recommendations ──────────────────────────────────
        recommendations = self.recommendation_engine.generate_recommendations(
            kpis, components, risks, ecrs, actions
        )

        # ── health score ─────────────────────────────────────
        # Use normalised 0-100 maturity values from components.
        # KPI variances are bounded at ±100 and normalised to 0-100.
        if components:
            comp_score = sum(c.get('maturity', 0) for c in components) / len(components)
        else:
            comp_score = 0.0

        if kpis:
            # Normalise: variance in [-100, 100] → score in [0, 100]
            kpi_score = sum(
                min(100, max(0, 50 + (k.get('variance') or 0)))
                for k in kpis
            ) / len(kpis)
        else:
            kpi_score = comp_score  # mirror component score if no KPIs

        crit_count = sum(1 for r in risks if (r.get('level') or '').lower() == 'critical')
        high_count = sum(1 for r in risks if (r.get('level') or '').lower() == 'high')
        risk_penalty = min(50, crit_count * 4 + high_count * 1)

        health_score = round(
            max(0.0, min(100.0,
                kpi_score * 0.35
                + comp_score * 0.45
                + (100 - risk_penalty) * 0.20
            )), 1
        )

        # ── risk resolution estimates ────────────────────────
        risk_resolution = [
            {
                'risk_id':        r.get('id', r.get('risk_id', '?')),
                'level':          r.get('level', '?'),
                'days_remaining': self.risk_analyzer.estimate_resolution_time(r),
            }
            for r in risks
            if (r.get('level') or '').lower() in ('critical', 'high')
        ]

        return {
            'timestamp':        datetime.utcnow().isoformat(),
            'health_score':     health_score,
            'domain_analysis':  domain_analysis,
            'release_readiness': release_readiness,
            'risk_hotspots':    hotspots,
            'risk_resolution':  risk_resolution,
            'recommendations':  recommendations,
            'summary': {
                'total_kpis':       len(kpis),
                'total_components': len(components),
                'total_risks':      len(risks),
                'total_ecrs':       len(ecrs),
                'total_actions':    len(actions),
                'critical_risks':   crit_count,
                'critical_components': sum(
                    1 for c in components
                    if (c.get('risk_level') or '').lower() == 'critical'
                ),
                'pending_ecrs': sum(
                    1 for e in ecrs
                    if (e.get('status') or '').lower() in ('pending', 'review')
                ),
                'open_actions': sum(
                    1 for a in actions
                    if (a.get('status') or '').lower() != 'closed'
                ),
            },
        }
