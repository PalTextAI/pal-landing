import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { MenuIcon, XIcon } from '@heroicons/react/outline';

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);

  const navItems = [
    { title: 'Home', path: 'hero' },
    { title: 'Features', path: 'features' },
    { title: 'How It Works', path: 'how-it-works' },
    { title: 'Advantages', path: 'advantages' },
    { title: 'Docs', path: '/docs', isExternal: true },
  ];

  const scrollToSection = (sectionId, isExternal) => {
    if (isExternal) return; // Don't scroll for external links
    
    const element = document.getElementById(sectionId);
    if (element) {
      setIsOpen(false); // Close mobile menu if open
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }
  };

  const menuVariants = {
    open: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.3,
        staggerChildren: 0.1,
        when: "beforeChildren"
      }
    },
    closed: {
      opacity: 0,
      y: -20,
      transition: {
        duration: 0.3
      }
    }
  };

  const itemVariants = {
    open: {
      opacity: 1,
      x: 0
    },
    closed: {
      opacity: 0,
      x: -20
    }
  };

  return (
    <motion.nav 
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
      className="fixed w-full z-50 bg-gray-900/80 backdrop-blur-md"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <motion.div 
            whileHover={{ scale: 1.05 }}
            className="flex-shrink-0"
          >
            <button 
              onClick={() => scrollToSection('hero')}
              className="text-2xl font-bold"
            >
              PalTextAI
            </button>
          </motion.div>
          
          {/* Desktop Menu */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              {navItems.map((item) => (
                <motion.div
                  key={item.title}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {item.isExternal ? (
                    <Link
                      to={item.path}
                      className="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700"
                    >
                      {item.title}
                    </Link>
                  ) : (
                    <button
                      onClick={() => scrollToSection(item.path)}
                      className="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700"
                    >
                      {item.title}
                    </button>
                  )}
                </motion.div>
              ))}
              <motion.div
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link
                  to="https://paltext-merchant.vercel.app/"
                  className="px-4 py-2 rounded-md text-sm font-medium bg-blue-600 hover:bg-blue-700 transition-colors"
                >
                  Get Started
                </Link>
              </motion.div>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none"
            >
              {isOpen ? (
                <XIcon className="block h-6 w-6" />
              ) : (
                <MenuIcon className="block h-6 w-6" />
              )}
            </motion.button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <motion.div
        initial="closed"
        animate={isOpen ? "open" : "closed"}
        variants={menuVariants}
        className={`md:hidden ${isOpen ? 'block' : 'hidden'}`}
      >
        <div className="px-2 pt-2 pb-3 space-y-1 bg-gray-900/95 backdrop-blur-lg">
          {navItems.map((item) => (
            <motion.div
              key={item.title}
              variants={itemVariants}
              whileTap={{ scale: 0.95 }}
            >
              {item.isExternal ? (
                <Link
                  to={item.path}
                  className="block px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:text-white hover:bg-gray-700"
                  onClick={() => setIsOpen(false)}
                >
                  {item.title}
                </Link>
              ) : (
                <button
                  onClick={() => scrollToSection(item.path)}
                  className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:text-white hover:bg-gray-700"
                >
                  {item.title}
                </button>
              )}
            </motion.div>
          ))}
          <motion.div
            variants={itemVariants}
            whileTap={{ scale: 0.95 }}
            className="mt-4"
          >
            <Link
              to="https://paltext-merchant.vercel.app/"
              className="block w-full text-center px-4 py-2 rounded-md text-sm font-medium bg-blue-600 hover:bg-blue-700 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              Get Started
            </Link>
          </motion.div>
        </div>
      </motion.div>
    </motion.nav>
  );
};

export default Navbar; 