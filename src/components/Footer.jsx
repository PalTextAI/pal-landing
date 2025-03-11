import { motion } from 'framer-motion';
import { FaGithub, FaTwitter, FaLinkedin, FaDiscord } from 'react-icons/fa';

const Footer = () => {
  const footerLinks = {
    Product: ['Features', 'Pricing', 'Documentation', 'API Reference'],
    Company: ['About Us', 'Contact'],
    Resources: [, 'Terms of Service'],
    Legal: ['Privacy Policy', 'Terms of Use', 'Cookie Policy']
  };

  const socialLinks = [
    { icon: FaTwitter, href: '#' },
    { icon: FaGithub, href: '#' },
    { icon: FaLinkedin, href: '#' },
    { icon: FaDiscord, href: '#' }
  ];

  return (
    <footer className="relative pt-20 pb-10 bg-gradient-to-b from-gray-900 to-black">
      {/* Decorative elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute left-0 -top-10 w-72 h-72 bg-purple-500/10 rounded-full filter blur-3xl" />
        <div className="absolute right-0 -bottom-10 w-72 h-72 bg-blue-500/10 rounded-full filter blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-4 relative z-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16">
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h3 className="text-white font-semibold mb-4">{category}</h3>
              <ul className="space-y-2">
                {links.map((link) => (
                  <motion.li
                    key={link}
                    whileHover={{ x: 5 }}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <a href="#">{link}</a>
                  </motion.li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-gray-800 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-4 md:mb-0">
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600"
              >
                PalTextAI
              </motion.div>
            </div>

            <div className="flex space-x-6">
              {socialLinks.map((social, index) => (
                <motion.a
                  key={index}
                  href={social.href}
                  whileHover={{ y: -3 }}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <social.icon size={24} />
                </motion.a>
              ))}
            </div>
          </div>

          <div className="mt-8 text-center text-gray-400 text-sm">
            <p>© {new Date().getFullYear()} PalTextAI. All rights reserved.</p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer; 