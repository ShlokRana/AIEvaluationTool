import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import styles from './Navbar.module.css';
import logo from '../../../../src/assets/logo/cerai-logo.png';
const Navbar: React.FC = () => {
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const location = useLocation();

  const navItems = [
    { 
      title: 'ACTIVITIES', 
      path: '/activities',
      dropdown: [
        { title: 'Workshops', path: '/activities/workshops' },
        { title: 'Hackathons', path: '/activities/hackathons' },
        { title: 'Seminars', path: '/activities/seminars' },
      ]
    },
    { 
      title: 'BLOGS', 
      path: '/blogs',
      dropdown: [
        { title: 'Latest Posts', path: '/blogs/latest' },
        { title: 'Categories', path: '/blogs/categories' },
      ]
    },
    { 
      title: 'COIN', 
      path: '/coin',
      dropdown: [
        { title: 'About COIN', path: '/coin/about' },
        { title: 'Get Started', path: '/coin/get-started' },
      ]
    },
    { 
      title: 'NEWS & EVENTS', 
      path: '/news-events',
      dropdown: [
        { title: 'Upcoming Events', path: '/news-events/upcoming' },
        { title: 'Past Events', path: '/news-events/past' },
      ]
    },
    { 
      title: 'PARTNERS', 
      path: '/partners',
      dropdown: [
        { title: 'Our Partners', path: '/partners/our-partners' },
        { title: 'Become a Partner', path: '/partners/become-partner' },
      ]
    },
    { 
      title: 'PEOPLE', 
      path: '/people',
      dropdown: [
        { title: 'Team', path: '/people/team' },
        { title: 'Alumni', path: '/people/alumni' },
      ]
    },
    { 
      title: 'CAREERS', 
      path: '/careers',
      dropdown: [
        { title: 'Open Positions', path: '/careers/positions' },
        { title: 'Internships', path: '/careers/internships' },
      ]
    },
    { 
      title: 'CONTACT', 
      path: '/contact',
      dropdown: [
        { title: 'Contact Us', path: '/contact' },
        { title: 'Support', path: '/contact/support' },
      ]
    },
  ];

  const toggleDropdown = (title: string) => {
    setActiveDropdown(activeDropdown === title ? null : title);
  };

  const isActive = (path: string) => {
    return location.pathname.startsWith(path) ? styles.active : '';
  };

  return (
    <nav className={styles.navbar}>
      <div className={styles.navContainer}>
        <Link to="/" className={styles.logo}>
  <img 
    src={logo} 
    alt="Logo" 
    className={styles.logoImage}
  />
</Link>
        
        {/* <div className={styles.navItems}>
          {navItems.map((item) => (
            <div 
              key={item.title} 
              className={`${styles.navItem} ${isActive(item.path)}`}
              onMouseEnter={() => toggleDropdown(item.title)}
              onMouseLeave={() => setActiveDropdown(null)}
            >
              <Link to={item.path} className={styles.navLink}>
                {item.title}
                {item.dropdown && <span className={styles.dropdownIcon}>▼</span>}
              </Link>
              
              {item.dropdown && activeDropdown === item.title && (
                <div className={styles.dropdown}>
                  {item.dropdown.map((subItem) => (
                    <Link 
                      key={subItem.path} 
                      to={subItem.path} 
                      className={styles.dropdownItem}
                    >
                      {subItem.title}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div> */}
      </div>
    </nav>
  );
};

export default Navbar;
