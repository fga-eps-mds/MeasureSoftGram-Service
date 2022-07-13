# Preconfig Atual
{
    # Caracteristicas
    "characteristic": {
        "reliability": { # Caracteristica 1
            "weight": 40,
            "subcharacteristic": { # SubCaracteristicas
                "testing_performance": { # SubCaracteristica 1
                    "weight": 30,
                    "metrics": { # Métricas da SubCaracteristica 1
                        "fast_tests": {
                            "weight": 100,
                        },
                    },
                },
                "testing_status": { # Subcaracteristica 2
                    "weight": 25,
                    "metrics": { # Métricas da subcaracteristica 2
                        "test_success": {
                            "weight": 100,
                        },
                    },
                },
                "product_stability": { # Subcaracteristica 3
                    "weight": 45,
                    "metrics": { # Métricas da subcaracteristica 3
                        "critical_issues_ratio": {
                            "weight": 50,
                        },
                        "build_stability": {
                            "weight": 50,
                        },
                    }
                },
            }
        },
        "maintainability": { # Caracteristicas 2
            "weight": 60,
            "factors": { # SubCaracteristicas
                "code_quality": {
                    "weight": 25,
                    "metrics": { # Métricas das SubCaracteristicas 2
                        "complexity": {
                            "weight": 50,
                        },
                        "duplication": {
                            "weight": 50,
                        }
                    }
                },

                "blocking_code": {
                    "weight": 75,
                    "metrics": {
                        "non_blocking_files": {
                            "weight": 100,
                        }
                    }
                }
            }
        }
    }
}