import mongoengine as me


class AnalysisComponents(me.Document):
    pre_config_id = me.StringField()
    sqc = me.DictField()
    aggregated_scs = me.DictField()
    aggregated_characteristics = me.DictField()
    weighted_measures = me.DictField()
    weighted_scs = me.DictField()
    weighted_c = me.DictField()

    def to_json(self):
        return {
            "pre_config_id": self.pre_config_id,
            "sqc": self.sqc,
            "aggregated_scs": self.aggregated_scs,
            "aggregated_characteristics": self.aggregated_characteristics,
            "weighted_measures": self.weighted_measures,
            "weighted_scs": self.weighted_scs,
            "weighted_c": self.weighted_c,
        }
