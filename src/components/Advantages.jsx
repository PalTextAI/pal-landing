import { motion } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import { ChatAlt2Icon, ShieldCheckIcon, GlobeAltIcon, LightningBoltIcon, UserGroupIcon } from '@heroicons/react/outline';

const advantages = [
  {
    title: "Works across channels",
    description: "Easily integrate your AI Agent with various platforms like Slack, WhatsApp, Messenger, and web widgets.",
    icon: GlobeAltIcon
  },
  {
    title: "Secure by default",
    description: "Your AI Agent ensures the utmost safety by refusing sensitive or unauthorized requests, keeping your data protected.",
    icon: ShieldCheckIcon
  },
  {
    title: "Enterprise quality guardrails",
    description: "AI-powered guardrails prevent misinformation and off-topic responses, maintaining professionalism and trust.",
    icon: LightningBoltIcon
  },
  {
    title: "Handles unclear requests",
    description: "Your AI Agent adapts to modern conversational styles, making interactions feel natural and relatable.",
    icon: ChatAlt2Icon
  },
  {
    title: "Enhance multilingual support",
    description: "Engage users globally with seamless language detection and translation in over 80+ languages.",
    icon: UserGroupIcon
  }
];

const Advantages = () => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  return (
    <section className="py-20 px-4 relative overflow-hidden" id="advantages">
      <div className="absolute inset-0 bg-gradient-to-b from-gray-900 to-black">
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
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
            Unlock the power of AI-driven Agents
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Experience the future of customer support with our advanced AI technology
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {advantages.map((advantage, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: index * 0.2 }}
              className="relative group"
            >
              <div className="p-6 bg-gray-800/50 backdrop-blur-lg rounded-xl hover:bg-gray-800/70 transition-all duration-300">
                <div className={`absolute inset-0 bg-gradient-to-r from-blue-600/10 to-purple-600/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl`} />
                <advantage.icon className="w-12 h-12 mb-4 text-purple-400" />
                <h3 className="text-xl font-semibold mb-3">{advantage.title}</h3>
                <p className="text-gray-400">{advantage.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Advantages; 