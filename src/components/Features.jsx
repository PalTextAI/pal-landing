import { motion } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import { LightningBoltIcon, CloudUploadIcon, ChartBarIcon, CogIcon } from '@heroicons/react/outline';

const features = [
  {
    title: "Lightning Fast Responses",
    description: "Get instant answers to customer queries with our AI-powered system",
    icon: LightningBoltIcon,
    color: "from-yellow-400 to-orange-500"
  },
  {
    title: "Easy FAQ Upload",
    description: "Simply upload your FAQ.json file and we'll handle the rest",
    icon: CloudUploadIcon,
    color: "from-blue-400 to-cyan-500"
  },
  {
    title: "Analytics Dashboard",
    description: "Track performance and gain insights with detailed analytics",
    icon: ChartBarIcon,
    color: "from-purple-400 to-pink-500"
  },
  {
    title: "Customizable Engine",
    description: "Fine-tune the AI to match your brand's voice and requirements",
    icon: CogIcon,
    color: "from-green-400 to-emerald-500"
  }
];

const Features = () => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const containerVariants = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.8,
        ease: "easeOut"
      }
    }
  };

  return (
    <section className="py-12 md:py-20 px-4 relative overflow-hidden" id="features">
      {/* Background decoration */}
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
          transition={{ duration: 0.8 }}
          className="text-center mb-8 md:mb-16"
        >
          <h2 className="text-3xl md:text-5xl font-bold mb-4 md:mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
            Powerful Features
          </h2>
          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto px-4">
            Everything you need to revolutionize your customer support experience
          </p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate={inView ? "visible" : "hidden"}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8"
        >
          {features.map((feature, index) => (
            <motion.div
              key={index}
              variants={itemVariants}
              className="relative group"
            >
              <div className="relative p-4 md:p-6 bg-gray-800/50 backdrop-blur-lg rounded-xl hover:bg-gray-800/70 transition-all duration-300">
                <div className={`absolute inset-0 bg-gradient-to-r ${feature.color} opacity-0 group-hover:opacity-10 rounded-xl transition-opacity duration-300`} />
                <feature.icon className="w-10 h-10 md:w-12 md:h-12 mb-3 md:mb-4 text-white" />
                <h3 className="text-lg md:text-xl font-semibold mb-2 md:mb-3">{feature.title}</h3>
                <p className="text-sm md:text-base text-gray-400">{feature.description}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default Features; 