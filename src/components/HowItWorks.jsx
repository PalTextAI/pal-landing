import { motion } from 'framer-motion';
import { useInView } from 'react-intersection-observer';

const steps = [
  {
    number: "01",
    title: "Build & deploy your agent",
    description: "Train an agent on your business data, configure the actions it can take, then deploy it for your customers."
  },
  {
    number: "02",
    title: "Agent solves your customers' problems",
    description: "The agent will answer questions and access external systems to gather data and take actions."
  },
  {
    number: "03",
    title: "Refine & optimize",
    description: "This ensures your agent is improving over time."
  },
  {
    number: "04",
    title: "Route complex issues to a human",
    description: "Seamlessly escalate certain queries to human agents when needed."
  }
];

const HowItWorks = () => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  return (
    <section className="py-20 px-4 relative overflow-hidden" id="how-it-works">
      <div className="absolute inset-0 bg-gradient-to-b from-gray-900 to-black">
        <div 
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `
              linear-gradient(to right, rgb(255 255 255 / 0.1) 1px, transparent 1px),
              linear-gradient(to bottom, rgb(255 255 255 / 0.1) 1px, transparent 1px)
            `,
            backgroundSize: '20px 20px'
          }}
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
            An end-to-end solution for conversational AI
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            With PalText, your customers can effortlessly find answers, resolve issues, and take meaningful actions.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: index * 0.2 }}
              className="relative group"
            >
              <div className="p-6 bg-gray-800/50 backdrop-blur-lg rounded-xl hover:bg-gray-800/70 transition-all duration-300">
                <div className={`absolute inset-0 bg-gradient-to-r from-blue-600/10 to-purple-600/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl`} />
                <span className="text-sm font-mono text-purple-400 mb-4 block">{step.number}</span>
                <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
                <p className="text-gray-400">{step.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks; 