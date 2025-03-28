import { motion } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import { FaGithub, FaLinkedin, FaTwitter } from 'react-icons/fa';

const team = [
  {
    name: "Bassey Goodluck",
    role: "Founder & CEO",
    image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80",
    bio: "AI enthusiast with 5+ years in Software Engineering",
    social: {
      twitter: "https://x.com/bassy_goodluck",
      linkedin: "#https://www.linkedin.com/in/goodluckbassey/",
      github: "https://github.com/Chrisszy123"
    }
  },
  {
    name: "Michael Chen",
    role: "CTO",
    image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80",
    bio: "Former Google AI researcher, NLP expert",
    social: {
      twitter: "#",
      linkedin: "#",
      github: "#"
    }
  },
  {
    name: "Emily Rodriguez",
    role: "Head of Product",
    image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80",
    bio: "Product strategist focused on AI solutions",
    social: {
      twitter: "#",
      linkedin: "#",
      github: "#"
    }
  },
  {
    name: "David Kim",
    role: "Lead Engineer",
    image: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80",
    bio: "Full-stack developer, AI infrastructure specialist",
    social: {
      twitter: "#",
      linkedin: "#",
      github: "#"
    }
  }
];

const Team = () => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  return (
    <section className="py-20 px-4 relative overflow-hidden" id="team">
      {/* Animated background */}
      <div className="absolute inset-0 bg-gradient-to-b from-gray-900 to-black">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 90, 0],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear"
          }}
          className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_50%_50%,_rgba(120,119,198,0.3),transparent_70%)]"
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
            Meet Our Team
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Passionate experts building the future of AI-powered customer support
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {team.map((member, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.8, delay: index * 0.2 }}
              className="relative group"
            >
              <div className="relative overflow-hidden rounded-xl bg-gray-800/50 backdrop-blur-lg p-6">
                <div className="absolute inset-0 bg-gradient-to-b from-blue-600/10 to-purple-600/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                
                <div className="relative z-10">
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    className="mb-6"
                  >
                    <img
                      src={member.image}
                      alt={member.name}
                      className="w-32 h-32 rounded-full mx-auto object-cover border-4 border-purple-500/30"
                    />
                  </motion.div>
                  
                  <h3 className="text-xl font-bold mb-2">{member.name}</h3>
                  <p className="text-purple-400 mb-3">{member.role}</p>
                  <p className="text-gray-400 mb-4">{member.bio}</p>
                  
                  <div className="flex justify-center space-x-4">
                    {Object.entries(member.social).map(([platform, link]) => (
                      <motion.a
                        key={platform}
                        href={link}
                        whileHover={{ scale: 1.2, rotate: 5 }}
                        className="text-gray-400 hover:text-white transition-colors"
                      >
                        {platform === 'twitter' && <FaTwitter size={20} />}
                        {platform === 'linkedin' && <FaLinkedin size={20} />}
                        {platform === 'github' && <FaGithub size={20} />}
                      </motion.a>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Team; 