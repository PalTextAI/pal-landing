import { motion } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import { CheckIcon } from '@heroicons/react/solid';

const plans = [
  {
    name: "Starter",
    price: "Free",
    features: [
      "1,000 queries per month",
      "Basic analytics",
      "1 FAQ dataset",
      "Community support"
    ],
    color: "from-blue-400 to-blue-600"
  },
  {
    name: "Pro",
    price: "$49",
    popular: true,
    features: [
      "50,000 queries per month",
      "Advanced analytics",
      "5 FAQ datasets",
      "Priority support",
      "Custom branding"
    ],
    color: "from-purple-400 to-purple-600"
  },
  {
    name: "Enterprise",
    price: "Custom",
    features: [
      "Unlimited queries",
      "Full analytics suite",
      "Unlimited datasets",
      "24/7 dedicated support",
      "Custom integration",
      "SLA guarantee"
    ],
    color: "from-pink-400 to-pink-600"
  }
];

const Pricing = () => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  return (
    <section className="py-20 px-4 relative" id="pricing">
      <div className="absolute inset-0 bg-gradient-to-b from-black to-gray-900">
        <motion.div
          animate={{
            backgroundPosition: ['0% 0%', '100% 100%'],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            repeatType: "reverse"
          }}
          className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_50%_50%,_rgba(66,108,245,0.3),transparent_70%)]"
        />
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
            Simple, Transparent Pricing
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Choose the perfect plan for your business needs
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.8, delay: index * 0.2 }}
              className="relative group"
            >
              <div className={`
                relative p-8 rounded-2xl
                ${plan.popular ? 'bg-gradient-to-b from-gray-800 to-gray-900' : 'bg-gray-800/50'}
                backdrop-blur-lg
                hover:transform hover:scale-105 transition-all duration-300
              `}>
                {plan.popular && (
                  <div className="absolute -top-4 left-0 right-0">
                    <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-1 rounded-full text-sm">
                      Most Popular
                    </span>
                  </div>
                )}
                
                <h3 className="text-2xl font-bold mb-4">{plan.name}</h3>
                <div className="mb-6">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  {plan.price !== "Custom" && <span className="text-gray-400">/month</span>}
                </div>
                
                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-center">
                      <CheckIcon className="h-5 w-5 text-green-500 mr-3" />
                      <span className="text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className={`
                    w-full py-3 px-6 rounded-lg font-medium
                    bg-gradient-to-r ${plan.color}
                    hover:opacity-90 transition-opacity
                  `}
                >
                  Get Started
                </motion.button>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Pricing; 