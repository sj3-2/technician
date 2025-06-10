// static/js/home_background.js
document.addEventListener('DOMContentLoaded', function() {
  // Wait for the hero section to be fully loaded
  setTimeout(initializeHeroParticles, 200);
  
  function initializeHeroParticles() {
    const heroWrapper = document.querySelector('.hero-content-wrapper');
    
    // If the hero wrapper doesn't exist, try again later or exit
    if (!heroWrapper) {
      console.log("Hero content wrapper not found, retrying in 200ms...");
      setTimeout(initializeHeroParticles, 200);
      return;
    }
    
    const canvas = document.createElement('canvas');
    canvas.id = 'hero-particles';
    
    const heroRect = heroWrapper.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    Object.assign(canvas.style, {
      position: 'absolute',
      top: (heroRect.top + scrollTop) + 'px',
      left: heroRect.left + 'px',
      width: heroRect.width + 'px',
      height: heroRect.height + 'px',
      zIndex: 1, 
      pointerEvents: 'none',
      opacity: 0,
      transition: 'opacity 2s ease-in-out'
    });
    
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    let width = heroRect.width;
    let height = heroRect.height;
    
    canvas.width = width;
    canvas.height = height;
    
    let centerX = width / 2;
    let centerY = height / 2;
    
    // Define the radius of the central "core" area
    let coreRadius = Math.min(width, height) * 0.3;
    // Define the max radius where particles can exist
    let maxRadius = Math.min(width, height) * 0.6;
    
    // Particle settings
    const particleCount = 20; // Increased count for better orbital effect
    const particles = [];
    
    const mouse = {
      x: null, 
      y: null,
      radius: 150
    };
    
    // Track mouse only when it's over the hero section
    heroWrapper.addEventListener('mousemove', function(event) {
      const rect = canvas.getBoundingClientRect();
      mouse.x = event.clientX - rect.left;
      mouse.y = event.clientY - rect.top;
    });
    
    heroWrapper.addEventListener('mouseleave', function() {
      mouse.x = null;
      mouse.y = null;
    });
    
    // Particle class with orbital motion
    class Particle {
      constructor() {
        // Instead of random positions, create particles with orbital parameters
        this.angle = Math.random() * Math.PI * 2;
        this.orbitRadius = Math.random() * (maxRadius - coreRadius) + coreRadius;
        
        this.x = centerX + Math.cos(this.angle) * this.orbitRadius;
        this.y = centerY + Math.sin(this.angle) * this.orbitRadius;
        
        // Save original orbit details for reference
        this.originalOrbitRadius = this.orbitRadius;
        
        // Rotation speed (positive for clockwise, negative for counter-clockwise)
        // Different particles move at different speeds for visual interest
        this.rotationSpeed = (Math.random() * 0.0015 + 0.0005) * (Math.random() > 0.5 ? 1 : -1);
        
        this.size = Math.random() * 3 + 1.5;
        this.density = (Math.random() * 25) + 5;
        
        this.calculateOpacity();
      }
      
      // Calculate opacity based on distance from center (closer = more visible)
      calculateOpacity() {
        // Calculate distance from center as a ratio (0 to 1)
        const distanceRatio = this.orbitRadius / maxRadius;
        // Inverse relationship: closer to center = more visible (higher opacity)
        // This creates an exponential falloff from center
        this.opacity = Math.max(0.1, 1 - (distanceRatio * 0.9));
        this.color = `rgba(255, 255, 255, ${this.opacity})`;
      }
      
      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.closePath();
        ctx.fillStyle = this.color;
        ctx.fill();
      }
      
      update() {
        // Begin with orbital motion - update angle
        this.angle += this.rotationSpeed;
        
        // Mouse interaction (if mouse is present)
        if (mouse.x !== null && mouse.y !== null) {
          const dx = mouse.x - this.x;
          const dy = mouse.y - this.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance < mouse.radius) {
            const forceDirectionX = dx / distance;
            const forceDirectionY = dy / distance;
            const force = (mouse.radius - distance) / mouse.radius;
            
            this.x -= forceDirectionX * force * this.density * 0.5;
            this.y -= forceDirectionY * force * this.density * 0.5;
            
            // Recalculate orbit radius based on new position
            const newDx = this.x - centerX;
            const newDy = this.y - centerY;
            this.orbitRadius = Math.sqrt(newDx * newDx + newDy * newDy);
            
            // Update angle based on new position
            this.angle = Math.atan2(newDy, newDx);
          }
        }
        
        // Gradually return to original orbit radius
        if (Math.abs(this.orbitRadius - this.originalOrbitRadius) > 0.1) {
          this.orbitRadius += (this.originalOrbitRadius - this.orbitRadius) * 0.03;
        }
        
        this.x = centerX + Math.cos(this.angle) * this.orbitRadius;
        this.y = centerY + Math.sin(this.angle) * this.orbitRadius;
        
        this.calculateOpacity();
        this.draw();
      }
    }
    
    function init() {
      particles.length = 0;
      for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
      }
    }
    
    function connectParticles() {
      const maxDistance = 120; // Reduced connect distance for cleaner appearance
      
      for (let i = 0; i < particles.length; i++) {
        for (let j = i; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance < maxDistance) {
            // Calculate opacity based on:
            // 1. Distance between particles
            // 2. Average opacity of the two particles (center proximity effect)
            const connectionOpacity = 
              (1 - distance / maxDistance) * 
              ((particles[i].opacity + particles[j].opacity) / 2) * 
              0.6; // Reduce overall line opacity
            
            ctx.strokeStyle = `rgba(255, 255, 255, ${connectionOpacity})`;
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }
    }
    
    function drawCenterGlow() {
      const gradient = ctx.createRadialGradient(
        centerX, centerY, 0,
        centerX, centerY, coreRadius * 1.5
      );
      gradient.addColorStop(0, 'rgba(255, 255, 255, 0.04)');
      gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
      
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, coreRadius * 1.5, 0, Math.PI * 2);
      ctx.fill();
    }
    
    function animate() {
      ctx.clearRect(0, 0, width, height);
      
      // Draw subtle background gradient
      const bgGradient = ctx.createRadialGradient(
        centerX, centerY, 0,
        centerX, centerY, maxRadius
      );
      bgGradient.addColorStop(0, 'rgba(10, 10, 20, 0.1)');
      bgGradient.addColorStop(1, 'rgba(5, 5, 15, 0.1)');
      ctx.fillStyle = bgGradient;
      ctx.fillRect(0, 0, width, height);
      
      // Draw center glow first (below particles)
      drawCenterGlow();
      connectParticles();
      
      for (let i = 0; i < particles.length; i++) {
        particles[i].update();
      }
      
      requestAnimationFrame(animate);
    }
    
    // Handle window resize
    window.addEventListener('resize', function() {
      const newHeroRect = heroWrapper.getBoundingClientRect();
      const newScrollTop = window.pageYOffset || document.documentElement.scrollTop;
      
      canvas.style.top = (newHeroRect.top + newScrollTop) + 'px';
      canvas.style.left = newHeroRect.left + 'px';
      canvas.style.width = newHeroRect.width + 'px';
      canvas.style.height = newHeroRect.height + 'px';
      
      width = newHeroRect.width;
      height = newHeroRect.height;
      canvas.width = width;
      canvas.height = height;
      
      centerX = width / 2;
      centerY = height / 2;
      coreRadius = Math.min(width, height) * 0.3;
      maxRadius = Math.min(width, height) * 0.6;
      
      init();
    });
    
    // Check if main content is loaded and fade in particles
    function checkForTextContent() {
      const titleElements = document.querySelectorAll('.hero-title .line');
      const description = document.querySelector('.hero-description');
      
      if (titleElements.length > 0 && description) {
        // Add delay to ensure text animations are complete
        setTimeout(function() {
          canvas.style.opacity = 1;
        }, 1500);
      } else {
        // Check again if not found
        setTimeout(checkForTextContent, 200);
      }
    }
    
    init();
    animate();
    checkForTextContent();
    
    // Reposition canvas on scroll
    window.addEventListener('scroll', function() {
      const updatedHeroRect = heroWrapper.getBoundingClientRect();
      const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;
      canvas.style.top = (updatedHeroRect.top + currentScrollTop) + 'px';
    });
  }
});