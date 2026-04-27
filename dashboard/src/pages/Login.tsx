import React, { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { useAuthStore } from "@/stores/auth";
import { useNavigate, Link } from "react-router-dom";
import { Wifi, Zap, Crown, CheckCircle2 } from "lucide-react";
import AppLogo from "@/components/AppLogo";

// Simple default plans for login page
const DEFAULT_PLANS = [
  {
    name: "Gratuito",
    description: "Perfecto para probar",
    price: "$0",
    period: "Siempre gratis",
    features: [
      { text: "1 Nodo incluido", included: true },
      { text: "Demo con 50 tickets gratis", included: true },
      { text: "Soporte por email", included: true },
      { text: "Más nodos", included: false },
      { text: "Tickets ilimitados", included: false },
    ],
    icon: Wifi,
    highlight: false,
  },
  {
    name: "Básico",
    description: "Pay-as-you-go",
    price: "$0.50",
    period: "por cada 50 tickets",
    features: [
      { text: "1 Nodo máximo", included: true },
      { text: "Tickets pagos después de demo", included: true },
      { text: "$0.50 c/50 tickets generados", included: true },
      { text: "Soporte prioritario", included: true },
      { text: "Más nodos", included: false },
    ],
    icon: Zap,
    highlight: false,
  },
  {
    name: "Pro",
    description: "Para empresas",
    price: "Contactar",
    period: "Planes personalizados",
    features: [
      { text: "Nodos ilimitados", included: true },
      { text: "Tickets ilimitados", included: true },
      { text: "API publica", included: true },
      { text: "Soporte 24/7", included: true },
      { text: "Consultoría técnica", included: true },
    ],
    icon: Crown,
    highlight: true,
  },
];

const Login: React.FC = () => {
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const login = useAuthStore((state) => state.login);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const success = await login(email, password);
    if (success) {
      navigate("/dashboard");
    } else {
      setError("Email o contraseña incorrectos. Por favor, inténtalo de nuevo.");
    }
    setIsLoading(false);
  };

  return (
    <div className="h-screen flex overflow-hidden">
      {/* Left side - Login Form (Centered, No Scroll) */}
      <div className="w-full lg:w-2/5 flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-900 dark:to-gray-800 p-6 overflow-hidden">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <AppLogo size="lg" className="shadow-lg" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">JADSlink</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Conectividad Satelital Comercial</p>
          </div>

          <Card className="border-0 shadow-xl">
            <CardContent className="pt-6 space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-center text-gray-900 dark:text-white">
                  Iniciar Sesión
                </h2>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium">
                    Email
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="tu@ejemplo.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={isLoading}
                    className="h-10"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium">
                    Contraseña
                  </Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={isLoading}
                    className="h-10"
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full h-10 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold shadow-md hover:shadow-lg transition-all"
                  disabled={isLoading}
                >
                  {isLoading ? "Cargando..." : "Iniciar Sesión"}
                </Button>
              </form>

              <div className="text-center text-sm">
                <span className="text-gray-600 dark:text-gray-400">¿No tienes cuenta? </span>
                <Link
                  to="/register"
                  className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                >
                  Regístrate aquí
                </Link>
              </div>

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                  Credenciales de demo:
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-300 text-center mt-1 font-mono bg-gray-100 dark:bg-gray-800 px-3 py-2 rounded">
                  admin@jads.com / admin123456
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Right side - Plans Description (Scrolleable) */}
      <div className="hidden lg:flex w-3/5 bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 flex-col overflow-y-auto">
        <div className="w-full flex items-start justify-center pt-8 pb-12">
          <div className="w-full max-w-4xl px-12">
            {/* Header Section */}
            <div className="text-center mb-12">
              <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
                Plataforma SaaS de<br />Conectividad Satelital
              </h2>
              <p className="text-sm text-blue-100 mb-2 max-w-2xl mx-auto">
                Vende acceso a internet satelital (Starlink) de forma comercial en buses, playas, eventos y zonas rurales.
              </p>
              <p className="text-xs text-blue-200 max-w-2xl mx-auto">
                Genera códigos QR, gestiona sesiones activas y monitorea tu infraestructura en tiempo real.
              </p>
            </div>

            {/* Plans Grid */}
            <div className="grid grid-cols-3 gap-4 mb-8">
              {DEFAULT_PLANS.map((plan: any, index: number) => {
                const IconComponent = plan.icon;
                const isHighlight = plan.highlight === true || index === 1;
                return (
                  <div
                    key={index}
                    className={`rounded-xl p-6 backdrop-blur-sm border transition-all h-full flex flex-col ${
                      isHighlight
                        ? "bg-gradient-to-br from-yellow-500/20 to-orange-500/20 border-yellow-400/50 ring-2 ring-yellow-400/50 scale-105"
                        : "bg-white/10 border-white/20 hover:bg-white/15 hover:border-white/30"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <div
                        className={`p-2 rounded-lg flex-shrink-0 ${
                          isHighlight
                            ? "bg-yellow-500/30"
                            : "bg-blue-500/30"
                        }`}
                      >
                        <IconComponent className={`w-5 h-5 ${
                          isHighlight
                            ? "text-yellow-300"
                            : "text-blue-300"
                        }`} />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-base font-bold text-white">{plan.name}</h3>
                        <p className="text-xs text-blue-200">{plan.description || ""}</p>
                      </div>
                    </div>

                    {isHighlight && (
                      <div className="mb-2 flex justify-center">
                        <span className="px-2 py-0.5 bg-yellow-500/30 text-yellow-300 text-xs font-semibold rounded-full">
                          ⭐ RECOMENDADO
                        </span>
                      </div>
                    )}

                    <div className="mb-4">
                      <p className="text-2xl font-bold text-white">{plan.price}</p>
                      <p className="text-xs text-blue-200 mt-0.5">{plan.period}</p>
                    </div>

                    <ul className="space-y-1.5 flex-1">
                      {plan.features.map((feature: any, fIndex: number) => (
                        <li key={fIndex} className="flex items-start gap-2">
                          <CheckCircle2
                            className={`w-3 h-3 flex-shrink-0 mt-0.5 ${
                              feature.included ? "text-green-400" : "text-gray-600"
                            }`}
                          />
                          <span
                            className={`text-xs leading-tight ${
                              feature.included ? "text-blue-100" : "text-gray-500"
                            }`}
                          >
                            {feature.text}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>

            {/* Features Section */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              {DEFAULT_PLANS.slice(0, 2).map((plan: any, index: number) => {
                const icon = index === 0 ? "✨" : "🚀";
                const planName = plan.name;
                const features = plan.features || [];
                return (
                  <div key={index} className="p-4 bg-white/10 backdrop-blur-sm rounded-lg border border-white/20">
                    <h4 className="text-white font-semibold mb-2 text-sm flex items-center gap-2">
                      {icon} {planName}
                    </h4>
                    <ul className="text-blue-100 text-xs space-y-1">
                      {features.slice(0, 4).map((feature: any, fIndex: number) => (
                        <li key={fIndex}>✓ {feature.text}</li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>

            {/* CTA Section */}
            <div className="text-center p-6 bg-gradient-to-r from-blue-500/20 to-indigo-500/20 backdrop-blur-sm rounded-xl border border-blue-400/30">
              <h4 className="text-white font-bold text-lg mb-1">
                Comienza con Plan Free
              </h4>
              <p className="text-blue-100 text-xs mb-3">
                50 tickets gratis + 1 nodo. Sin tarjeta de crédito.
              </p>
              <Link to="/register">
                <Button className="bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white font-semibold px-6 py-2 text-sm">
                  Crear Cuenta Ahora →
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
