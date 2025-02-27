import { useEffect } from "react";
import PricingSection from "../Pricing/PricingSection";

export default function LandingPage() {
  useEffect(() => {
    const scrollToHash = () => {
      const hash = window.location.hash;
      if (hash) {
        const elementId = hash.substring(1);
        const element = document.getElementById(elementId);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth' });
        } else {
          setTimeout(scrollToHash, 100);
        }
      }
    };

    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    const redirectTo = urlParams.get('redirectTo');

    if (redirectTo) {
      window.location.hash = `#${redirectTo}`;
    }

    scrollToHash();

    window.addEventListener('hashchange', scrollToHash);

    return () => {
      window.removeEventListener('hashchange', scrollToHash);
    };
  }, []);

  useEffect(() => {
    const originalTheme = document.documentElement.getAttribute("data-theme");
    document.documentElement.setAttribute("data-theme", "light");
    document.documentElement.style.colorScheme = "light";
    function playAnimation(element: any, frame = false) {
      if (frame) {
        element.style.visibility = "visible";
        element.style.opacity = "1";
        element.style.transform = "none";
      }
      if (
        element.getBoundingClientRect().top > 0 &&
        element.getBoundingClientRect().top <= window.innerHeight * 0.75
      ) {
        element.classList.add("lambdagency-animate-init");
      }
    }

    function prepareAnimation(doc: any, frame = false) {
      const elements = doc.getElementsByClassName("lambdagency-animate");

      for (let element of elements) {
        if (frame) {
          playAnimation(element, true);
        } else {
          playAnimation(element);

          window.addEventListener("scroll", () => playAnimation(element));
        }
      }
    }

    prepareAnimation(document);

    const timer = setTimeout(() => {
      const iframe = document.getElementsByClassName(
        "edit-site-visual-editor__editor-canvas"
      );
      const innerDoc =
        iframe.length > 0
          ? (iframe[0] as HTMLIFrameElement).contentDocument ||
            (iframe[0] as HTMLIFrameElement).contentWindow?.document
          : null;

      if (innerDoc) {
        prepareAnimation(innerDoc, true);
      }
    }, 6000);

    return () => {
      clearTimeout(timer);
      document.documentElement.setAttribute(
        "data-theme",
        originalTheme || "dark"
      );
      document.documentElement.style.colorScheme = originalTheme || "dark";
    };
  }, []);

  return (
    <div className="light-theme">
      <meta charSet="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <meta name="robots" content="max-image-preview:large" />
      <title>λgency - Empowering Your Career with AI</title>
      <script src="/landing-page/js/emoji.js"></script>
      <link
        rel="stylesheet"
        id="block-cover-css"
        href="/landing-page/css/style_cover.min.css?ver=6.6.2"
        media="all"
      />
      <link
        id="block-image-inline-css"
        rel="stylesheet"
        href="/landing-page/css/block-image-inline.css"
      />
      <link
        id="block-paragraph-inline-css"
        rel="stylesheet"
        href="/landing-page/css/block-paragraph-inline.css"
      />
      <link
        id="block-heading-inline-css"
        rel="stylesheet"
        href="/landing-page/css/block-heading-inline.css"
      />
      <link
        id="block-button-inline-css"
        rel="stylesheet"
        href="/landing-page/css/block-button-inline.css"
      />
      <link
        id="block-buttons-inline-css"
        rel="stylesheet"
        href="/landing-page/css/block-buttons-inline.css"
      />
      <link
        id="block-columns-inline-css"
        rel="stylesheet"
        href="/landing-page/css/block-columns-inline.css"
      />
      <link
        id="block-site-title-inline-css"
        rel="stylesheet"
        href="/landing-page/css/block-site-title-inline.css"
      />
      <link
        id="emoji-styles-inline-css"
        rel="stylesheet"
        href="/landing-page/css/emoji-styles-inline.css"
      />
      <link
        id="block-library-inline-css"
        rel="stylesheet"
        href="/landing-page/css/block-library-inline.css"
      />
      <link
        rel="stylesheet"
        id="presset-css"
        href="/landing-page/css/presset.css?ver=1.0.1"
        media="all"
      />
      <link
        rel="stylesheet"
        id="custom-styling-css"
        href="/landing-page/css/custom-styling.css?ver=1.0.1"
        media="all"
      />
      <link
        id="global-styles-inline-css"
        rel="stylesheet"
        href="/landing-page/css/global-styles-inline.css"
      />
      <link
        id="core-block-supports-inline-css"
        rel="stylesheet"
        href="/landing-page/css/core-block-supports-inline.css"
      />
      <link
        id="block-template-skip-link-inline-css"
        rel="stylesheet"
        href="/landing-page/css/block-template-skip-link-inline.css"
      />
      <link
        id="fonts-local"
        rel="stylesheet"
        href="/landing-page/css/fonts-local.css"
      />
      <link
        rel="icon"
        href="/landing-page/img/cropped-a-logo-azul-32x32.png"
        sizes="32x32"
      />
      <link
        rel="icon"
        href="/landing-page/img/cropped-a-logo-azul-192x192.png"
        sizes="192x192"
      />
      <link
        rel="apple-touch-icon"
        href="/landing-page/img/cropped-a-logo-azul-180x180.png"
      />
      <meta
        name="msapplication-TileImage"
        content="/landing-page/img/cropped-a-logo-azul-270x270.png"
      />
      <div className="site-blocks">
        <header className="block-template-part">
          <div
            className="block-group is-style-customboxshadow is-layout-constrained container-core-group-is-layout-2 block-group-is-layout-constrained"
            style={{
              borderBottomColor: "var(---preset--color--theme-7)",
              borderBottomWidth: 1,
              paddingTop: 10,
              paddingRight: 20,
              paddingBottom: 10,
              paddingLeft: 20,
            }}
          >
            <div className="block-group is-content-justification-space-between is-layout-flex container-core-group-is-layout-1 block-group-is-layout-flex">
              <figure className="block-image size-full is-resized">
                <a href="/">
                  <img
                    decoding="async"
                    width={1000}
                    height={1000}
                    src="/landing-page/img/a-logo-1.png"
                    className="image-74"
                    style={{ width: 34, height: "auto" }}
                    srcSet="/landing-page/img/a-logo-1.png 1000w, /landing-page/img/a-logo-1-300x300.png 300w, /landing-page/img/a-logo-1-100x100.png 100w, /landing-page/img/a-logo-1-600x600.png 600w, /landing-page/img/a-logo-1-150x150.png 150w, /landing-page/img/a-logo-1-768x768.png 768w"
                    sizes="(max-width: 1000px) 100vw, 1000px"
                  />
                </a>
              </figure>
              <div className="guten-element guten-nav-menu guten-f9BEGq fast">
                <nav
                  className="main-nav"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "flex-end",
                    gap: "40px",
                  }}
                >
                  {/* Login Link */}
                  <a
                    href="/login"
                    className="has-text-color has-link-color has-inter-font-family"
                    style={{
                      fontSize: 16,
                      fontWeight: 600,
                      color: "#1a2c2a",
                      textDecoration: "none",
                    }}
                  >
                    Login
                  </a>
                  {/* Register Button */}
                  <a
                    href="/signup/"
                    className="has-text-color has-link-color has-inter-font-family"
                    style={{
                      fontSize: 16,
                      fontWeight: 600,
                      color: "#1a2c2a",
                      textDecoration: "none",
                    }}
                  >
                    Register
                  </a>
                </nav>
              </div>
            </div>
          </div>
        </header>
        <div className="block-group is-layout-flow block-group-is-layout-flow">
          <div
            className="block-cover is-repeated has-aspect-ratio"
            style={{
              paddingTop: 96,
              paddingRight: 20,
              paddingBottom: 0,
              paddingLeft: 20,
              aspectRatio: "auto",
              minHeight: "unset",
            }}
            id="home"
          >
            <span
              aria-hidden="true"
              className="block-cover__background has-background-dim-100 has-background-dim block-cover__gradient-background has-background-gradient"
              style={{
                background:
                  "linear-gradient(180deg,rgba(255,255,255,0) 0%,rgb(255,255,255) 100%)",
              }}
            />
            <div
              className="block-cover__image-background image-441 is-repeated"
              style={{
                backgroundPosition: "0% 15%",
                backgroundImage: "url(/landing-page/img/dot-pattern.webp)",
              }}
            ></div>
            <div className="block-cover__inner-container is-layout-constrained container-core-cover-is-layout-1 block-cover-is-layout-constrained">
              <div className="block-columns is-layout-flex container-core-columns-is-layout-1 block-columns-is-layout-flex">
                <div className="block-column is-layout-flow block-column-is-layout-flow">
                  <div
                    className="block-group lambdagency-animate lambdagency-move-up is-content-justification-center is-nowrap is-layout-flex container-core-group-is-layout-4 block-group-is-layout-flex"
                    style={{ marginBottom: 15 }}
                  >
                    <div
                      className="block-group has-theme-7-background-color has-background is-layout-constrained container-core-group-is-layout-3 block-group-is-layout-constrained"
                      style={{
                        borderRadius: 5,
                        paddingTop: 6,
                        paddingRight: 11,
                        paddingBottom: 6,
                        paddingLeft: 11,
                      }}
                    >
                      <p
                        className="has-theme-3-color has-text-color has-link-color has-inter-font-family elements-390f66538e176f1d9d802a1f08df4092"
                        style={{
                          fontSize: 16,
                          fontStyle: "normal",
                          fontWeight: 600,
                          lineHeight: "1.3",
                        }}
                      >
                        New
                      </p>
                    </div>
                    <p
                      className="has-theme-2-color has-text-color has-inter-font-family"
                      style={{ fontSize: 16 }}
                    >
                      Your AI Recruitment Partner
                    </p>
                  </div>
                  <h1
                    className="block-heading has-text-align-center lambdagency-animate lambdagency-move-up lambdagency-delay-1 has-theme-0-color has-text-color has-link-color has-inter-font-family has-h-1-font-size elements-2a7173c76cc3b30913daf86d5a5c5b0e"
                    style={{
                      fontStyle: "normal",
                      fontWeight: 700,
                      letterSpacing: "-0.01em",
                      lineHeight: "1.1",
                    }}
                  >
                    Get Hired Quickly: Automate Your Job Hunt with AI!
                  </h1>
                  <div
                    className="block-group lambdagency-animate lambdagency-move-up lambdagency-delay-3 is-layout-flow block-group-is-layout-flow"
                    style={{ marginTop: 10 }}
                  >
                    <p
                      className="has-text-align-center has-theme-2-color has-text-color"
                      style={{ fontSize: 22 }}
                    >
                      Escape from the Endless Manual Job Hunt.
                    </p>
                  </div>
                  <div
                    className="block-buttons has-custom-font-size lambdagency-animate lambdagency-move-up lambdagency-delay-5 has-inter-font-family is-content-justification-center is-layout-flex container-core-buttons-is-layout-1 block-buttons-is-layout-flex"
                    style={{ marginTop: 40, fontSize: 18 }}
                  >
                    <div
                      className="block-button has-custom-font-size is-style-custombuttonstyle1 has-inter-font-family"
                      style={{
                        fontSize: 18,
                        fontStyle: "normal",
                        fontWeight: 600,
                        lineHeight: 1,
                      }}
                    >
                      <a
                        className="block-button__link element-button"
                        href="/signup/"
                        style={{
                          borderRadius: 10,
                          paddingTop: 20,
                          paddingRight: 30,
                          paddingBottom: 20,
                          paddingLeft: 30,
                        }}
                      >
                        Get Started
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div
          className="block-group has-background is-layout-constrained container-core-group-is-layout-9 block-group-is-layout-constrained"
          style={{
            // background:
            // "linear-gradient(180deg,rgb(255,255,255) 34%,rgb(237,250,255) 100%)",
            paddingTop: 100,
            paddingRight: 20,
            paddingBottom: 0,
            paddingLeft: 20,
          }}
        >
          <div className="block-columns is-layout-flex container-core-columns-is-layout-2 block-columns-is-layout-flex">
            <div className="block-column lambdagency-margin-bottom-n140 lambdagency-z-index-10 is-layout-flow block-column-is-layout-flow">
              <div
                className="block-cover duotone-grayscale"
                style={{
                  borderTopLeftRadius: 20,
                  borderTopRightRadius: 20,
                  borderBottomLeftRadius: 0,
                  borderBottomRightRadius: 0,
                  minHeight: 490,
                  aspectRatio: "unset",
                }}
              >
                <span
                  aria-hidden="true"
                  className="block-cover__background has-background-dim-0 has-background-dim"
                  style={{ backgroundColor: "#746563" }}
                />
                <img
                  width={2560}
                  height={1707}
                  className="block-cover__image-background image-171"
                  src="/landing-page/img/stressed-developer-scaled.jpg"
                  style={{ objectPosition: "70% 18%" }}
                  data-object-fit="cover"
                  data-object-position="70% 18%"
                  srcSet="/landing-page/img/stressed-developer-scaled.jpg 2560w, /landing-page/img/stressed-developer-300x200.jpg 300w, /landing-page/img/stressed-developer-1024x683.jpg 1024w, /landing-page/img/stressed-developer-768x512.jpg 768w, /landing-page/img/stressed-developer-1536x1024.jpg 1536w, /landing-page/img/stressed-developer-2048x1365.jpg 2048w, /landing-page/img/stressed-developer-1320x880.jpg 1320w, /landing-page/img/stressed-developer-600x400.jpg 600w"
                  sizes="(max-width: 2560px) 100vw, 2560px"
                />
                <div className="block-cover__inner-container is-layout-flow block-cover-is-layout-flow">
                  <p className="has-text-align-center has-large-font-size" />
                </div>
              </div>
              <div
                className="block-group has-theme-0-background-color has-background is-layout-flow block-group-is-layout-flow"
                style={{
                  borderBottomLeftRadius: 20,
                  borderBottomRightRadius: 20,
                  paddingTop: 20,
                  paddingRight: 20,
                  paddingBottom: 20,
                  paddingLeft: 20,
                }}
              >
                <div className="block-group is-content-justification-center is-nowrap is-layout-flex container-core-group-is-layout-7 block-group-is-layout-flex">
                  <p
                    className="has-white-color has-text-color has-link-color has-inter-font-family elements-eff855357591079224bcda3fce4cc2df"
                    style={{
                      fontSize: 16,
                      fontStyle: "normal",
                      fontWeight: 700,
                    }}
                  >
                    Feeling stuck in your job search?{" "}
                  </p>
                  <p
                    className="has-theme-2-color has-text-color has-inter-font-family"
                    style={{ fontSize: 16 }}
                  >
                    Let our AI take the wheel and navigate you to your next big
                    opportunity.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div
          id="about"
          className="block-group is-layout-flow block-group-is-layout-flow"
        >
          <div
            className="block-cover is-repeated"
            style={{
              paddingTop: 240,
              paddingRight: 20,
              paddingBottom: 120,
              paddingLeft: 20,
            }}
          >
            <span
              aria-hidden="true"
              className="block-cover__background has-background-dim-100 has-background-dim block-cover__gradient-background has-background-gradient"
              style={{
                background:
                  "linear-gradient(180deg,rgba(255,255,255,0) 0%,rgb(255,255,255) 100%)",
              }}
            />
            <div
              className="block-cover__image-background image-441 is-repeated"
              style={{
                backgroundPosition: "0% 5%",
                backgroundImage: "url(/landing-page/img/dot-pattern.webp)",
              }}
            ></div>
            <div className="block-cover__inner-container is-layout-constrained container-core-cover-is-layout-3 block-cover-is-layout-constrained">
              <div className="block-columns is-not-stacked-on-mobile is-layout-flex container-core-columns-is-layout-3 block-columns-is-layout-flex">
                <div
                  className="block-column is-vertically-aligned-center is-layout-flow block-column-is-layout-flow"
                  style={{ marginLeft: "0.5em", flexBasis: "40%" }}
                >
                  <div
                    className="block-group is-vertical is-content-justification-left is-layout-flex container-core-group-is-layout-11 block-group-is-layout-flex"
                    style={{ minHeight: 405 }}
                  >
                    <div
                      className="block-group has-theme-7-background-color has-background has-inter-font-family is-nowrap is-layout-flex container-core-group-is-layout-10 block-group-is-layout-flex"
                      style={{
                        borderRadius: 5,
                        paddingTop: 6,
                        paddingRight: 11,
                        paddingBottom: 6,
                        paddingLeft: 11,
                      }}
                    >
                      <h3
                        className="block-heading has-theme-3-color has-text-color has-link-color has-inter-font-family elements-43abd3f090e345ebcbfd29f8859b8511"
                        style={{
                          fontSize: 16,
                          fontStyle: "normal",
                          fontWeight: 600,
                          lineHeight: "1.3",
                        }}
                      >
                        Who we are
                      </h3>
                    </div>
                    <p
                      className="has-theme-2-color has-text-color has-link-color has-inter-font-family elements-bd4a0a69218eba56c2af9e4d88a04c59"
                      style={{ fontSize: 18 }}
                    >
                      <strong>Advanced AI Recruitment</strong>
                    </p>
                  </div>
                </div>
                <div
                  className="block-column is-vertically-aligned-center is-layout-flow block-column-is-layout-flow"
                  style={{ marginLeft: "0.5em", flexBasis: "60%" }}
                >
                  <div className="block-group is-nowrap is-layout-flex container-core-group-is-layout-12 block-group-is-layout-flex">
                    <h2
                      className="block-heading has-text-align-left has-theme-0-color has-text-color has-link-color has-h-2-alt-font-size elements-9e421b4a9c755fed6bc6a3ebccf78979 container-content-1"
                      style={{
                        marginBottom: 30,
                        fontStyle: "normal",
                        fontWeight: 600,
                        textTransform: "capitalize",
                      }}
                    >
                      Innovating Job Searches with AI
                    </h2>
                  </div>
                  <p
                    className="has-theme-2-color has-text-color"
                    style={{ marginBottom: 15 }}
                  >
                    At λgency, we're rethinking the old-school job search
                    process. By applying AI to handle the routine tasks that bog
                    you down, we're making job hunting a bit simpler and more
                    efficient. We're a young startup—only a few months in—and
                    we're excited to see how these practical tweaks can really
                    help both job seekers and recruiters.
                  </p>
                  <p className="has-theme-2-color has-text-color">
                    Our innovative platform enables job seekers to automatically
                    apply to hundreds of job opportunities with personalized,
                    AI-generated PDF resumes tailored for each specific
                    position. This not only maximizes your chances of getting
                    noticed but also significantly accelerates the hiring
                    process.
                  </p>
                  <div
                    className="block-group is-layout-flex container-core-group-is-layout-16 block-group-is-layout-flex"
                    style={{ paddingTop: 35 }}
                  >
                    <div
                      className="block-group has-border-color is-layout-constrained container-core-group-is-layout-13 block-group-is-layout-constrained"
                      style={{
                        borderColor: "#e5e5e5",
                        borderWidth: 1,
                        borderRadius: 5,
                        paddingTop: 8,
                        paddingRight: 12,
                        paddingBottom: 8,
                        paddingLeft: 12,
                      }}
                    >
                      <p
                        className="has-theme-2-color has-text-color"
                        style={{ fontSize: 16, lineHeight: 1 }}
                      >
                        Automatic
                      </p>
                    </div>
                    <div
                      className="block-group has-border-color is-layout-constrained container-core-group-is-layout-14 block-group-is-layout-constrained"
                      style={{
                        borderColor: "#e5e5e5",
                        borderWidth: 1,
                        borderRadius: 5,
                        paddingTop: 8,
                        paddingRight: 12,
                        paddingBottom: 8,
                        paddingLeft: 12,
                      }}
                    >
                      <p
                        className="has-theme-2-color has-text-color"
                        style={{ fontSize: 16, lineHeight: 1 }}
                      >
                        Fast
                      </p>
                    </div>
                    <div
                      className="block-group has-border-color is-layout-constrained container-core-group-is-layout-15 block-group-is-layout-constrained"
                      style={{
                        borderColor: "#e5e5e5",
                        borderWidth: 1,
                        borderRadius: 5,
                        paddingTop: 8,
                        paddingRight: 12,
                        paddingBottom: 8,
                        paddingLeft: 12,
                      }}
                    >
                      <p
                        className="has-theme-2-color has-text-color"
                        style={{ fontSize: 16, lineHeight: 1 }}
                      >
                        Problem Solver
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div
          className="block-group is-layout-flow block-group-is-layout-flow"
          style={{
            paddingTop: "var(---preset--spacing--30)",
            paddingRight: "5vw",
            paddingBottom: "var(---preset--spacing--30)",
            paddingLeft: "5vw",
          }}
        >
          <div
            className="block-group is-vertical is-content-justification-center is-layout-flex container-core-group-is-layout-20 block-group-is-layout-flex"
            style={{ marginBottom: 70 }}
          >
            <div
              className="block-group has-theme-7-background-color has-background has-inter-font-family is-nowrap is-layout-flex container-core-group-is-layout-18 block-group-is-layout-flex"
              style={{
                borderRadius: 5,
                paddingTop: 0,
                paddingRight: 11,
                paddingBottom: 0,
                paddingLeft: 11,
              }}
            >
              <h3
                className="block-heading has-theme-3-color has-text-color has-link-color has-inter-font-family elements-524d3acddef7af3f27e3ff560f798e4d"
                style={{
                  fontSize: 16,
                  fontStyle: "normal",
                  fontWeight: 600,
                  lineHeight: "1.3",
                }}
              >
                Awesome Opportunities
              </h3>
            </div>
            <h2
              className="block-heading has-text-align-center has-theme-0-color has-text-color has-link-color has-h-1-alt-font-size elements-1b144df071cbc0a505598bf01cc8d564"
              style={{
                fontStyle: "normal",
                fontWeight: 600,
                letterSpacing: "-0.02em",
                lineHeight: "1.2",
              }}
            >
              Work With The Best!
            </h2>
            <div className="block-group is-content-justification-center is-nowrap is-layout-flex container-core-group-is-layout-19 block-group-is-layout-flex">
              <p
                className="has-text-align-center has-theme-2-color has-text-color has-link-color elements-7ea0440752315ff2e03a3d8ade74e660 container-content-2"
                style={{ fontSize: 18 }}
              >
                Apply to leading companies in the tech industry and secure
                top-tier positions.
              </p>
            </div>
          </div>
          <div
            className="block-columns has-border-color is-layout-flex container-core-columns-is-layout-4 block-columns-is-layout-flex"
            style={{ borderColor: "#d2fae5", borderWidth: 1, borderRadius: 20 }}
          >
            <div
              className="block-column is-vertically-aligned-center is-layout-flow block-column-is-layout-flow"
              style={{
                borderRightColor: "var(---preset--color--theme-7)",
                borderRightWidth: 1,
                paddingTop: 60,
                paddingBottom: 60,
              }}
            >
              <figure className="block-image aligncenter size-full is-resized duotone-rgb106108108-ccc-1">
                <img
                  width={1024}
                  height={347}
                  src="/landing-page/img/Google_2015_logo.svg_.png"
                  className="image-100"
                  style={{ width: 135, height: "auto" }}
                  srcSet="/landing-page/img/Google_2015_logo.svg_.png 1024w, /landing-page/img/Google_2015_logo.svg_-300x102.png 300w, /landing-page/img/Google_2015_logo.svg_-768x260.png 768w, /landing-page/img/Google_2015_logo.svg_-600x203.png 600w"
                  sizes="(max-width: 1024px) 100vw, 1024px"
                />
              </figure>
            </div>
            <div
              className="block-column is-vertically-aligned-center is-layout-flow block-column-is-layout-flow"
              style={{
                borderRightColor: "var(---preset--color--theme-7)",
                borderRightWidth: 1,
                paddingTop: 60,
                paddingBottom: 60,
              }}
            >
              <figure className="block-image aligncenter size-full is-resized duotone-rgb106108108-ccc-2">
                <img
                  width={603}
                  height={182}
                  src="/landing-page/img/Amazon_logo.png"
                  className="image-101"
                  style={{ width: 135 }}
                  srcSet="/landing-page/img/Amazon_logo.png 603w, /landing-page/img/Amazon_logo-300x91.png 300w, /landing-page/img/Amazon_logo-600x181.png 600w"
                  sizes="(max-width: 603px) 100vw, 603px"
                />
              </figure>
            </div>
            <div
              className="block-column is-vertically-aligned-center is-layout-flow block-column-is-layout-flow"
              style={{
                borderRightColor: "var(---preset--color--theme-7)",
                borderRightWidth: 1,
                paddingTop: 60,
                paddingBottom: 60,
              }}
            >
              <figure className="block-image aligncenter size-full is-resized duotone-rgb106108108-ccc-3">
                <img
                  width={3000}
                  height={604}
                  src="/landing-page/img/1664035558meta-logo-png.png"
                  className="image-102"
                  style={{ width: 135 }}
                  srcSet="/landing-page/img/1664035558meta-logo-png.png 3000w, /landing-page/img/1664035558meta-logo-png-300x60.png 300w, /landing-page/img/1664035558meta-logo-png-1024x206.png 1024w, /landing-page/img/1664035558meta-logo-png-768x155.png 768w, /landing-page/img/1664035558meta-logo-png-1536x309.png 1536w, /landing-page/img/1664035558meta-logo-png-2048x412.png 2048w, /landing-page/img/1664035558meta-logo-png-1320x266.png 1320w, /landing-page/img/1664035558meta-logo-png-600x121.png 600w"
                  sizes="(max-width: 3000px) 100vw, 3000px"
                />
              </figure>
            </div>
            <div
              className="block-column is-vertically-aligned-center is-layout-flow block-column-is-layout-flow"
              style={{
                borderRightColor: "var(---preset--color--theme-7)",
                borderRightWidth: 1,
                paddingTop: 60,
                paddingBottom: 60,
              }}
            >
              <figure className="block-image aligncenter size-full is-resized duotone-rgb106108108-ccc-4">
                <img
                  width={2424}
                  height={829}
                  src="/landing-page/img/apple-11.png"
                  className="image-103"
                  style={{ width: 135 }}
                  srcSet="/landing-page/img/apple-11.png 2424w, /landing-page/img/apple-11-300x103.png 300w, /landing-page/img/apple-11-1024x350.png 1024w, /landing-page/img/apple-11-768x263.png 768w, /landing-page/img/apple-11-1536x525.png 1536w, /landing-page/img/apple-11-2048x700.png 2048w, /landing-page/img/apple-11-1320x451.png 1320w, /landing-page/img/apple-11-600x205.png 600w"
                  sizes="(max-width: 2424px) 100vw, 2424px"
                />
              </figure>
            </div>
            <div
              className="block-column is-vertically-aligned-center is-layout-flow block-column-is-layout-flow"
              style={{
                borderRightColor: "var(---preset--color--theme-7)",
                borderRightWidth: 1,
                paddingTop: 60,
                paddingBottom: 60,
              }}
            >
              <figure className="block-image aligncenter size-full is-resized duotone-rgb106108108-ccc-5">
                <img
                  width={2226}
                  height={678}
                  src="/landing-page/img/Logonetflix.png"
                  className="image-104"
                  style={{ width: 170 }}
                  srcSet="/landing-page/img/Logonetflix.png 2226w, /landing-page/img/Logonetflix-300x91.png 300w, /landing-page/img/Logonetflix-1024x312.png 1024w, /landing-page/img/Logonetflix-768x234.png 768w, /landing-page/img/Logonetflix-1536x468.png 1536w, /landing-page/img/Logonetflix-2048x624.png 2048w, /landing-page/img/Logonetflix-1320x402.png 1320w, /landing-page/img/Logonetflix-600x183.png 600w"
                  sizes="(max-width: 2226px) 100vw, 2226px"
                />
              </figure>
            </div>
            <div
              className="block-column is-vertically-aligned-center is-layout-flow block-column-is-layout-flow"
              style={{ paddingTop: 60, paddingBottom: 60 }}
            >
              <figure className="block-image aligncenter size-full is-resized duotone-rgb106108108-ccc-6">
                <img
                  width={2350}
                  height={515}
                  src="/landing-page/img/Microsoft-Logo.wine_-e1726452235243.png"
                  className="image-105"
                  style={{ width: 135 }}
                  srcSet="/landing-page/img/Microsoft-Logo.wine_-e1726452235243.png 2350w, /landing-page/img/Microsoft-Logo.wine_-e1726452235243-300x66.png 300w, /landing-page/img/Microsoft-Logo.wine_-e1726452235243-1024x224.png 1024w, /landing-page/img/Microsoft-Logo.wine_-e1726452235243-768x168.png 768w, /landing-page/img/Microsoft-Logo.wine_-e1726452235243-1536x337.png 1536w, /landing-page/img/Microsoft-Logo.wine_-e1726452235243-2048x449.png 2048w, /landing-page/img/Microsoft-Logo.wine_-e1726452235243-1320x289.png 1320w, /landing-page/img/Microsoft-Logo.wine_-e1726452235243-600x131.png 600w"
                  sizes="(max-width: 2350px) 100vw, 2350px"
                />
              </figure>
            </div>
          </div>
        </div>
        <div
          id="services"
          className="block-group has-background is-layout-constrained container-core-group-is-layout-31 block-group-is-layout-constrained"
          style={{
            // background:
            //   "linear-gradient(180deg,rgb(255,255,255) 0%,rgb(237,250,255) 100%)",
            paddingTop: 100,
            paddingRight: 20,
            paddingBottom: 0,
            paddingLeft: 20,
          }}
        >
          <div
            className="block-group is-vertical is-content-justification-center is-layout-flex container-core-group-is-layout-24 block-group-is-layout-flex"
            style={{ marginBottom: 70 }}
          >
            <div
              className="block-group has-theme-7-background-color has-background has-inter-font-family is-nowrap is-layout-flex container-core-group-is-layout-22 block-group-is-layout-flex"
              style={{
                borderRadius: 5,
                paddingTop: 6,
                paddingRight: 11,
                paddingBottom: 6,
                paddingLeft: 11,
              }}
            >
              <h3
                className="block-heading has-theme-3-color has-text-color has-link-color has-inter-font-family elements-a5276f46b8067db3a5a83964a07b0ccd"
                style={{
                  fontSize: 16,
                  fontStyle: "normal",
                  fontWeight: 600,
                  lineHeight: "1.3",
                }}
              >
                Our Services
              </h3>
            </div>
            <h2
              className="block-heading has-text-align-center has-theme-0-color has-text-color has-link-color has-h-1-alt-font-size elements-33eca300a0035ce2b76fcbd0206f51dd"
              style={{
                fontStyle: "normal",
                fontWeight: 600,
                letterSpacing: "-0.02em",
                lineHeight: "1.2",
              }}
            >
              AI-Driven Job Hunter
            </h2>
            <div className="block-group is-content-justification-center is-nowrap is-layout-flex container-core-group-is-layout-23 block-group-is-layout-flex">
              <p
                className="has-text-align-center has-theme-2-color has-text-color has-link-color elements-9ce3fe055bcdee5fdbaaba1b3079c193 container-content-3"
                style={{ fontSize: 18 }}
              >
                Simplify your job search with our AI technology that matches you
                with the right opportunities and applies on your behalf.
              </p>
            </div>
          </div>
          <div className="block-columns is-layout-flex container-core-columns-is-layout-6 block-columns-is-layout-flex">
            <div className="block-column lambdagency-margin-bottom-n120 lambdagency-z-index-10 is-layout-flow block-column-is-layout-flow">
              <div
                className="block-columns is-layout-flex container-core-columns-is-layout-5 block-columns-is-layout-flex"
                style={{ borderRadius: 20 }}
              >
                <div className="block-column is-vertically-aligned-bottom is-layout-flow block-column-is-layout-flow">
                  <div
                    className="block-group has-theme-1-background-color has-background is-vertical is-content-justification-center is-layout-flex container-core-group-is-layout-26 block-group-is-layout-flex"
                    style={{
                      borderTopLeftRadius: 20,
                      borderBottomLeftRadius: 20,
                      minHeight: 500,
                    }}
                  >
                    <figure className="block-image size-full is-resized lambdagency-animate lambdagency-move-up">
                      <img
                        width={2000}
                        height={2000}
                        src="/landing-page/img/lupa-e1726761986333.png"
                        className="image-152"
                        style={{ width: 263, height: "auto" }}
                        srcSet="/landing-page/img/lupa-e1726761986333.png 2000w, /landing-page/img/lupa-e1726761986333-300x300.png 300w, /landing-page/img/lupa-e1726761986333-1024x1024.png 1024w, /landing-page/img/lupa-e1726761986333-150x150.png 150w, /landing-page/img/lupa-e1726761986333-768x768.png 768w, /landing-page/img/lupa-e1726761986333-1536x1536.png 1536w, /landing-page/img/lupa-e1726761986333-1320x1320.png 1320w, /landing-page/img/lupa-e1726761986333-600x600.png 600w, /landing-page/img/lupa-e1726761986333-100x100.png 100w"
                        sizes="(max-width: 2000px) 100vw, 2000px"
                      />
                    </figure>
                    <div
                      className="block-group is-vertical is-layout-flex container-core-group-is-layout-25 block-group-is-layout-flex"
                      style={{
                        paddingTop: 25,
                        paddingRight: 40,
                        paddingBottom: 40,
                        paddingLeft: 40,
                      }}
                    >
                      <h3
                        className="block-heading has-white-color has-text-color has-link-color has-h-3-font-size elements-a7624683b71eec2bfecfb600d33d6206"
                        style={{
                          fontStyle: "normal",
                          fontWeight: 600,
                          letterSpacing: "-0.01em",
                          lineHeight: "1.3",
                        }}
                      >
                        Job Hunting
                      </h3>
                      <p
                        className="has-theme-2-color has-text-color"
                        style={{ fontSize: 16 }}
                      >
                        Our AI filters and applies to job openings that align
                        with your skills and interests.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="block-column is-layout-flow block-column-is-layout-flow">
                  <div
                    className="block-group has-background is-vertical is-content-justification-center is-layout-flex container-core-group-is-layout-28 block-group-is-layout-flex"
                    style={{
                      background:
                        "linear-gradient(180deg,rgb(12, 207, 188) 0%,rgb(0, 118, 108) 100%)",
                      minHeight: 500,
                    }}
                  >
                    <figure className="block-image size-full is-resized lambdagency-animate lambdagency-move-up lambdagency-delay-3">
                      <img
                        width={2000}
                        height={2000}
                        src="/landing-page/img/Checklist_bw-e1726761947998.png"
                        className="image-158"
                        style={{ width: 265, height: "auto" }}
                        srcSet="/landing-page/img/Checklist_bw-e1726761947998.png 2000w, /landing-page/img/Checklist_bw-e1726761947998-300x300.png 300w, /landing-page/img/Checklist_bw-e1726761947998-1024x1024.png 1024w, /landing-page/img/Checklist_bw-e1726761947998-150x150.png 150w, /landing-page/img/Checklist_bw-e1726761947998-768x768.png 768w, /landing-page/img/Checklist_bw-e1726761947998-1536x1536.png 1536w, /landing-page/img/Checklist_bw-e1726761947998-1320x1320.png 1320w, /landing-page/img/Checklist_bw-e1726761947998-600x600.png 600w, /landing-page/img/Checklist_bw-e1726761947998-100x100.png 100w"
                        sizes="(max-width: 2000px) 100vw, 2000px"
                      />
                    </figure>
                    <div
                      className="block-group is-vertical is-layout-flex container-core-group-is-layout-27 block-group-is-layout-flex"
                      style={{
                        paddingTop: 25,
                        paddingRight: 40,
                        paddingBottom: 40,
                        paddingLeft: 40,
                      }}
                    >
                      <h3
                        className="block-heading has-white-color has-text-color has-link-color has-h-3-font-size elements-c050b074276b37cc9f9e0c216a1427a9"
                        style={{
                          fontStyle: "normal",
                          fontWeight: 600,
                          letterSpacing: "-0.01em",
                          lineHeight: "1.3",
                        }}
                      >
                        Deep Analysis
                      </h3>
                      <p
                        className="has-text-color"
                        style={{ color: "#ffffffb3", fontSize: 16 }}
                      >
                        Gain insights into job descriptions to better understand
                        how you fit with potential employers.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="block-column is-style-customboxshadow2 is-layout-flow block-column-is-layout-flow">
                  <div
                    className="block-group has-border-color has-theme-7-border-color has-white-background-color has-background is-vertical is-content-justification-center is-layout-flex container-core-group-is-layout-30 block-group-is-layout-flex"
                    style={{
                      borderWidth: 1,
                      borderTopRightRadius: 20,
                      borderBottomRightRadius: 20,
                      minHeight: 500,
                    }}
                  >
                    <figure className="block-image size-full is-resized lambdagency-animate lambdagency-move-up lambdagency-delay-5">
                      <img
                        width={2000}
                        height={2000}
                        src="/landing-page/img/cv.png"
                        className="image-153"
                        style={{ width: 245, height: "auto" }}
                        srcSet="/landing-page/img/cv.png 2000w, /landing-page/img/cv-300x300.png 300w, /landing-page/img/cv-1024x1024.png 1024w, /landing-page/img/cv-150x150.png 150w, /landing-page/img/cv-768x768.png 768w, /landing-page/img/cv-1536x1536.png 1536w, /landing-page/img/cv-1320x1320.png 1320w, /landing-page/img/cv-600x600.png 600w, /landing-page/img/cv-100x100.png 100w"
                        sizes="(max-width: 2000px) 100vw, 2000px"
                      />
                    </figure>
                    <div
                      className="block-group is-vertical is-layout-flex container-core-group-is-layout-29 block-group-is-layout-flex"
                      style={{
                        paddingTop: 0,
                        paddingRight: 40,
                        paddingBottom: 40,
                        paddingLeft: 40,
                      }}
                    >
                      <h3
                        className="block-heading has-black-color has-text-color has-link-color has-h-3-font-size elements-1e83722664d95592f37d57ba7cbf96c1"
                        style={{
                          fontStyle: "normal",
                          fontWeight: 600,
                          letterSpacing: "-0.01em",
                          lineHeight: "1.3",
                        }}
                      >
                        AI-Generated Data
                      </h3>
                      <p
                        className="has-theme-2-color has-text-color"
                        style={{ fontSize: 16 }}
                      >
                        Get tailored resumes and responses crafted by AI to
                        enhance your application for each job.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="block-group is-layout-flow block-group-is-layout-flow">
          <div
            className="block-cover is-repeated"
            style={{
              marginTop: 0,
              marginBottom: 0,
              paddingTop: 185,
              paddingRight: 20,
              paddingBottom: 0,
              paddingLeft: 20,
            }}
          >
            <span
              aria-hidden="true"
              className="block-cover__background has-background-dim-100 has-background-dim block-cover__gradient-background has-background-gradient"
              style={{
                background:
                  "linear-gradient(180deg,rgba(255,255,255,0) 0%,rgb(255,255,255) 100%)",
              }}
            />
            <div
              className="block-cover__image-background image-441 is-repeated"
              style={{
                backgroundPosition: "0% 15%",
                backgroundImage: "url(/landing-page/img/dot-pattern.webp)",
              }}
            ></div>
            <div className="block-cover__inner-container is-layout-constrained container-core-cover-is-layout-4 block-cover-is-layout-constrained">
              <p className="has-text-align-center has-theme-0-color has-text-color has-link-color elements-af80cd34a8a1ea6821415c4a8409b68b">
                Your Trusted AI Partner
              </p>
              <div className="block-group is-layout-constrained container-core-group-is-layout-36 block-group-is-layout-constrained">
                <div
                  className="block-columns is-layout-flex container-core-columns-is-layout-7 block-columns-is-layout-flex"
                  style={{ marginTop: 40 }}
                >
                  <div className="block-column is-layout-flow block-column-is-layout-flow">
                    <div className="block-group is-vertical is-content-justification-center is-layout-flex container-core-group-is-layout-32 block-group-is-layout-flex">
                      <h3
                        className="block-heading has-theme-0-color has-text-color has-link-color elements-368a8a9df93ddf1965a0a50a412e7765"
                        style={{
                          fontSize: 43,
                          fontStyle: "normal",
                          fontWeight: 700,
                        }}
                      >
                        90%
                      </h3>
                      <p
                        className="has-theme-2-color has-text-color has-link-color elements-12109e4c5dfe891c2d7fdde5ad24b987"
                        style={{
                          fontSize: 18,
                          fontStyle: "normal",
                          fontWeight: 400,
                        }}
                      >
                        More Interviews
                      </p>
                    </div>
                  </div>
                  <div className="block-column is-layout-flow block-column-is-layout-flow">
                    <div className="block-group is-vertical is-content-justification-center is-layout-flex container-core-group-is-layout-33 block-group-is-layout-flex">
                      <h3
                        className="block-heading has-theme-0-color has-text-color has-link-color elements-d1bca9ab699301f0d5e2f29c5e128bfe"
                        style={{
                          fontSize: 43,
                          fontStyle: "normal",
                          fontWeight: 700,
                        }}
                      >
                        24/7
                      </h3>
                      <p
                        className="has-theme-2-color has-text-color has-link-color elements-d623745259960ab69a35f61bfeaffd41"
                        style={{
                          fontSize: 18,
                          fontStyle: "normal",
                          fontWeight: 400,
                        }}
                      >
                        Job Hunting
                      </p>
                    </div>
                  </div>
                  <div className="block-column is-layout-flow block-column-is-layout-flow">
                    <div className="block-group is-vertical is-content-justification-center is-layout-flex container-core-group-is-layout-34 block-group-is-layout-flex">
                      <h3
                        className="block-heading has-theme-0-color has-text-color has-link-color elements-3a4336b7574ddadfa44d38a46c0e316c"
                        style={{
                          fontSize: 43,
                          fontStyle: "normal",
                          fontWeight: 700,
                        }}
                      >
                        1100 +
                      </h3>
                      <p
                        className="has-theme-2-color has-text-color has-link-color elements-dbf0ef0be94ac7d76e827a73d4e35ab8"
                        style={{
                          fontSize: 18,
                          fontStyle: "normal",
                          fontWeight: 400,
                        }}
                      >
                        Trusted by Developers
                      </p>
                    </div>
                  </div>
                  <div className="block-column is-layout-flow block-column-is-layout-flow">
                    <div className="block-group is-vertical is-content-justification-center is-layout-flex container-core-group-is-layout-35 block-group-is-layout-flex">
                      <h3
                        className="block-heading has-theme-0-color has-text-color has-link-color elements-ba044ff47fe6b44bb852a33acf299547"
                        style={{
                          fontSize: 43,
                          fontStyle: "normal",
                          fontWeight: 700,
                        }}
                      >
                        15 K
                      </h3>
                      <p
                        className="has-theme-2-color has-text-color has-link-color elements-b17a47eadee1009eb4c58e7dbdee41a9"
                        style={{
                          fontSize: 18,
                          fontStyle: "normal",
                          fontWeight: 400,
                        }}
                      >
                        Interviews Scheduled
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div
          className="block-group is-layout-flow block-group-is-layout-flow"
          style={{
            paddingTop: 70,
            paddingRight: "5vw",
            paddingBottom: 0,
            paddingLeft: "5vw",
          }}
        >
          <div className="block-group is-vertical is-content-justification-center is-layout-flex container-core-group-is-layout-54 block-group-is-layout-flex">
            <div
              className="block-group has-theme-7-background-color has-background has-inter-font-family is-nowrap is-layout-flex container-core-group-is-layout-38 block-group-is-layout-flex"
              style={{
                borderRadius: 5,
                paddingTop: 6,
                paddingRight: 11,
                paddingBottom: 6,
                paddingLeft: 11,
              }}
            >
              <h3
                className="block-heading has-theme-3-color has-text-color has-link-color has-inter-font-family elements-a833603c2dc5af035655815f78e3946f"
                style={{
                  fontSize: 16,
                  fontStyle: "normal",
                  fontWeight: 600,
                  lineHeight: "1.3",
                }}
              >
                Our Testimonial
              </h3>
            </div>
            <h2
              className="block-heading has-text-align-center has-theme-0-color has-text-color has-link-color has-h-1-alt-font-size elements-369534e3574e46fc63cc8c715451d251"
              style={{
                fontStyle: "normal",
                fontWeight: 600,
                letterSpacing: "-0.02em",
                lineHeight: "1.2",
              }}
            >
              Client’s experiences
            </h2>
            <div className="block-group is-content-justification-center is-nowrap is-layout-flex container-core-group-is-layout-39 block-group-is-layout-flex">
              <p
                className="has-text-align-center has-theme-2-color has-text-color has-link-color elements-80d49c26bf1ab5eb4096efe8c342a75e container-content-4"
                style={{ fontSize: 18 }}
              >
                Hear It from Our Early Adopters
              </p>
            </div>
            <div
              className="block-columns is-layout-flex container-core-columns-is-layout-8 block-columns-is-layout-flex"
              style={{ paddingTop: 80, paddingBottom: 20 }}
            >
              <div className="block-column is-vertically-aligned-center null-radius-10 is-layout-flow block-column-is-layout-flow">
                <div
                  className="block-group has-border-color has-theme-7-border-color is-layout-constrained container-core-group-is-layout-42 block-group-is-layout-constrained"
                  style={{
                    borderWidth: 1,
                    borderRadius: 20,
                    paddingTop: 40,
                    paddingRight: 40,
                    paddingBottom: 40,
                    paddingLeft: 40,
                  }}
                >
                  <div className="block-group is-horizontal is-content-justification-space-between is-nowrap is-layout-flex container-core-group-is-layout-41 block-group-is-layout-flex">
                    <div className="block-group is-vertical is-layout-flex container-core-group-is-layout-40 block-group-is-layout-flex">
                      <h3
                        className="block-heading has-theme-0-color has-text-color has-link-color elements-453415e6537d9aff40a9d18b4e93307b"
                        style={{
                          fontSize: 22,
                          fontStyle: "normal",
                          fontWeight: 600,
                        }}
                      >
                        Devendra Kumar
                      </h3>
                      <p
                        className="has-theme-2-color has-text-color has-link-color elements-a3bb7621c0751810f3c8098dc6cf8d51"
                        style={{ fontSize: 16 }}
                      >
                        Engineer
                      </p>
                    </div>
                    <figure className="block-image size-full is-resized">
                      <img
                        src="/landing-page/img/icon-quote.svg"
                        className="image-584"
                        style={{
                          width: 50,
                          filter:
                            "invert(42%) sepia(68%) saturate(450%) hue-rotate(145deg) brightness(93%) contrast(88%) opacity(20%)",
                        }}
                      />
                    </figure>
                  </div>
                  <p
                    className="has-theme-2-color has-text-color has-link-color elements-d7f86abb5483e87c135136eb16410c17"
                    style={{
                      fontSize: 18,
                      fontStyle: "normal",
                      fontWeight: 400,
                    }}
                  >
                    “I just wanted to thank you for the incredible service
                    λgency provides. I landed a job in less than a month! Your
                    AI really knows its stuff, matching me with a position that
                    needed my exact skill set.”
                  </p>
                </div>
              </div>
              <div className="block-column null-radius-10 is-layout-flow block-column-is-layout-flow">
                <div
                  className="block-group has-border-color has-theme-7-border-color is-layout-constrained container-core-group-is-layout-45 block-group-is-layout-constrained"
                  style={{
                    borderWidth: 1,
                    borderRadius: 20,
                    paddingTop: 40,
                    paddingRight: 40,
                    paddingBottom: 40,
                    paddingLeft: 40,
                  }}
                >
                  <div className="block-group is-horizontal is-content-justification-space-between is-nowrap is-layout-flex container-core-group-is-layout-44 block-group-is-layout-flex">
                    <div className="block-group is-vertical is-layout-flex container-core-group-is-layout-43 block-group-is-layout-flex">
                      <h3
                        className="block-heading has-theme-0-color has-text-color has-link-color elements-831b5545ada0dd9743cf1272ba817004"
                        style={{
                          fontSize: 22,
                          fontStyle: "normal",
                          fontWeight: 600,
                        }}
                      >
                        Daniel Carvalho
                      </h3>
                      <p
                        className="has-theme-2-color has-text-color has-link-color elements-efab80d5870c231812cba7e858e8bd94"
                        style={{ fontSize: 16 }}
                      >
                        Tech Lead
                      </p>
                    </div>
                    <figure className="block-image size-full is-resized">
                      <img
                        src="/landing-page/img/icon-quote.svg"
                        className="image-584"
                        style={{
                          width: 50,
                          filter:
                            "invert(42%) sepia(68%) saturate(450%) hue-rotate(145deg) brightness(93%) contrast(88%) opacity(20%)",
                        }}
                      />
                    </figure>
                  </div>
                  <p
                    className="has-theme-2-color has-text-color has-link-color elements-a5c4400bb0ef8a76d1b09bf7dcadd8a5"
                    style={{
                      fontSize: 18,
                      fontStyle: "normal",
                      fontWeight: 400,
                    }}
                  >
                    “Hey team, just dropping a note to say your system works
                    wonders. I’ve gotten more callbacks in the past two weeks
                    than I did in the last six months. You guys are into
                    something big here.”
                  </p>
                </div>
              </div>
              <div className="block-column null-radius-10 is-layout-flow block-column-is-layout-flow">
                <div
                  className="block-group has-border-color has-theme-7-border-color is-layout-constrained container-core-group-is-layout-48 block-group-is-layout-constrained"
                  style={{
                    borderWidth: 1,
                    borderRadius: 20,
                    paddingTop: 40,
                    paddingRight: 40,
                    paddingBottom: 40,
                    paddingLeft: 40,
                  }}
                >
                  <div className="block-group is-horizontal is-content-justification-space-between is-nowrap is-layout-flex container-core-group-is-layout-47 block-group-is-layout-flex">
                    <div className="block-group is-vertical is-layout-flex container-core-group-is-layout-46 block-group-is-layout-flex">
                      <h3
                        className="block-heading has-theme-0-color has-text-color has-link-color elements-cf7f82d850303c57f882ae9521b17f46"
                        style={{
                          fontSize: 22,
                          fontStyle: "normal",
                          fontWeight: 600,
                        }}
                      >
                        Daan Meijer
                      </h3>
                      <p
                        className="has-theme-2-color has-text-color has-link-color elements-0be6f8a727fdeed4f8a9e7d224e607a9"
                        style={{ fontSize: 16 }}
                      >
                        Lead QA Analyst
                      </p>
                    </div>
                    <figure className="block-image size-full is-resized">
                      <img
                        src="/landing-page/img/icon-quote.svg"
                        className="image-584"
                        style={{
                          width: 50,
                          filter:
                            "invert(42%) sepia(68%) saturate(450%) hue-rotate(145deg) brightness(93%) contrast(88%) opacity(20%)",
                        }}
                      />
                    </figure>
                  </div>
                  <p
                    className="has-theme-2-color has-text-color has-link-color elements-f2ce30179238889fbb1061a7ae3ffad3"
                    style={{
                      fontSize: 18,
                      fontStyle: "normal",
                      fontWeight: 400,
                    }}
                  >
                    “I was really impressed with how your AI took the time to
                    understand the intricacies of each job posting. It’s like
                    you’ve built a bridge directly to employers. Thanks for
                    making job hunting less daunting.”
                  </p>
                </div>
              </div>
              <div className="block-column null-radius-10 is-layout-flow block-column-is-layout-flow">
                <div
                  className="block-group has-border-color has-theme-7-border-color is-layout-constrained container-core-group-is-layout-51 block-group-is-layout-constrained"
                  style={{
                    borderWidth: 1,
                    borderRadius: 20,
                    paddingTop: 40,
                    paddingRight: 40,
                    paddingBottom: 40,
                    paddingLeft: 40,
                  }}
                >
                  <div className="block-group is-horizontal is-content-justification-space-between is-nowrap is-layout-flex container-core-group-is-layout-50 block-group-is-layout-flex">
                    <div className="block-group is-vertical is-layout-flex container-core-group-is-layout-49 block-group-is-layout-flex">
                      <h3
                        className="block-heading has-theme-0-color has-text-color has-link-color elements-16d4b3ddefbea2a199bf4ada0ce8981b"
                        style={{
                          fontSize: 22,
                          fontStyle: "normal",
                          fontWeight: 600,
                        }}
                      >
                        Chris Thompson
                      </h3>
                      <p
                        className="has-theme-2-color has-text-color has-link-color elements-747f27872c36615e4b46ee0912a52186"
                        style={{ fontSize: 16 }}
                      >
                        Full Stack Developer
                      </p>
                    </div>
                    <figure className="block-image size-full is-resized">
                      <img
                        src="/landing-page/img/icon-quote.svg"
                        className="image-584"
                        style={{
                          width: 50,
                          filter:
                            "invert(42%) sepia(68%) saturate(450%) hue-rotate(145deg) brightness(93%) contrast(88%) opacity(20%)",
                        }}
                      />
                    </figure>
                  </div>
                  <p
                    className="has-theme-2-color has-text-color has-link-color elements-9f89778db13673ef5a6d72c7021fc873"
                    style={{
                      fontSize: 18,
                      fontStyle: "normal",
                      fontWeight: 400,
                    }}
                  >
                    “I have to say, I was blown away by how accurately your AI
                    mapped out the job landscape based on my skills. It’s
                    refreshing to see such a tailored approach in job
                    applications.”
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
        <PricingSection />
        <div
          className="block-group is-layout-constrained container-core-group-is-layout-60 block-group-is-layout-constrained"
          style={{
            marginTop: 0,
            marginBottom: 0,
            paddingTop: "var(---preset--spacing--40)",
            paddingRight: 20,
            paddingBottom: "var(---preset--spacing--30)",
            paddingLeft: 20,
          }}
        >
          <div
            className="block-columns lambdagency-margin-top-n70 lambdagency-z-index-10 is-layout-flex container-core-columns-is-layout-9 block-columns-is-layout-flex"
            style={{
              paddingTop: "var(---preset--spacing--80)",
              paddingBottom: "var(---preset--spacing--80)",
            }}
          >
            <div className="block-column is-style-customboxshadow2 is-layout-flow block-column-is-layout-flow">
              <div
                className="block-group has-white-background-color has-background is-layout-flow block-group-is-layout-flow"
                style={{
                  borderTopLeftRadius: 20,
                  borderTopRightRadius: 20,
                  borderTopColor: "#d2fae5",
                  borderTopWidth: 1,
                  borderRightColor: "#d2fae5",
                  borderRightWidth: 1,
                  borderLeftColor: "#d2fae5",
                  borderLeftWidth: 1,
                  paddingTop: 50,
                  paddingRight: 40,
                  paddingBottom: 50,
                  paddingLeft: 40,
                }}
              >
                <div className="block-group is-content-justification-space-between is-layout-flex container-core-group-is-layout-57 block-group-is-layout-flex">
                  <div className="block-group is-vertical is-content-justification-stretch is-layout-flex container-core-group-is-layout-56 block-group-is-layout-flex">
                    <h3
                      className="block-heading has-black-color has-text-color has-link-color has-inter-font-family has-h-2-font-size elements-0729e009d6499ed8d6742a59d5adf131"
                      style={{ fontStyle: "normal", fontWeight: 600 }}
                    >
                      Secure Your Next Job Opportunity!
                    </h3>
                    <p />
                    <p
                      className="has-theme-2-color has-text-color has-link-color elements-f67cd70c7098b78e31882c9d6e2ac8f5"
                      style={{ fontSize: 18 }}
                    >
                      Subscribe to our revolutionary service and let our
                      advanced AI{" "}
                    </p>
                    <p
                      className="has-theme-2-color has-text-color has-link-color elements-f6c1851aac081d9dca6e14e3a2d1543a"
                      style={{ fontSize: 18 }}
                    >
                      scout the best job opportunities for you, day and night.
                      Simplify{" "}
                    </p>
                    <p
                      className="has-theme-2-color has-text-color has-link-color elements-a35453075ce728d614e3258dffe9e127"
                      style={{ fontSize: 18 }}
                    >
                      your job search with a solution designed to find and apply
                      to jobs{" "}
                    </p>
                    <p
                      className="has-theme-2-color has-text-color has-link-color elements-bad57ef3053f86e546760622b5414891"
                      style={{ fontSize: 18 }}
                    >
                      that match your skills and aspirations.
                    </p>
                  </div>
                  <div className="block-buttons is-content-justification-right is-layout-flex container-core-buttons-is-layout-2 block-buttons-is-layout-flex">
                    <div
                      className="block-button has-custom-font-size is-style-custombuttonstyle1"
                      style={{
                        fontSize: 18,
                        fontStyle: "normal",
                        fontWeight: 600,
                        lineHeight: 1,
                      }}
                    >
                      <a
                        className="block-button__link element-button"
                        href="/signup/"
                        style={{
                          borderRadius: 10,
                          paddingTop: 20,
                          paddingRight: 30,
                          paddingBottom: 20,
                          paddingLeft: 30,
                        }}
                      >
                        Start Now
                      </a>
                    </div>
                  </div>
                </div>
              </div>
              <div
                className="block-group has-theme-1-background-color has-background is-layout-constrained block-group-is-layout-constrained"
                style={{
                  borderBottomLeftRadius: 20,
                  borderBottomRightRadius: 20,
                  paddingTop: 18,
                  paddingBottom: 18,
                }}
              >
                <p
                  className="has-text-align-center has-theme-2-color has-text-color has-link-color elements-4f28a23d6cb194db7e2b44712934b0ee"
                  style={{ fontSize: 16 }}
                >
                  Empower your career with continuous, automated job
                  applications tailored just for you.
                </p>
              </div>
            </div>
          </div>
        </div>
        <footer
          style={{
            backgroundColor: "#fff",
            padding: "10px 20px",
            borderTop: "1px solid #e2e8f0",
            marginTop: "40px",
          }}
        >
          <div
            style={{
              maxWidth: "1200px",
              margin: "0 auto",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            {/* Navigation Links */}
            <nav
              style={{
                marginTop: "20px",
                marginBottom: "20px",
                display: "flex",
                gap: "40px",
                flexWrap: "wrap",
                justifyContent: "center",
              }}
            >
              <a
                href="/#home"
                style={{
                  color: "#2d3748",
                  fontWeight: 600,
                  fontSize: "16px",
                  textDecoration: "none",
                }}
              >
                Home
              </a>
              <a
                href="/#about"
                style={{
                  color: "#2d3748",
                  fontWeight: 600,
                  fontSize: "16px",
                  textDecoration: "none",
                }}
              >
                About
              </a>
              <a
                href="/#pricing"
                style={{
                  color: "#2d3748",
                  fontWeight: 600,
                  fontSize: "16px",
                  textDecoration: "none",
                }}
              >
                Pricing
              </a>
              <a
                href="/#support"
                style={{
                  color: "#2d3748",
                  fontWeight: 600,
                  fontSize: "16px",
                  textDecoration: "none",
                }}
              >
                Support
              </a>
              <a
                href="/#terms"
                style={{
                  color: "#2d3748",
                  fontWeight: 600,
                  fontSize: "16px",
                  textDecoration: "none",
                }}
              >
                Terms &amp; Conditions
              </a>
            </nav>

            {/* Agency Info (Optional) */}
            <div
              style={{
                textAlign: "center",
                color: "#718096",
                fontSize: "14px",
              }}
            >
              <p>Powered by λgency</p>
              <p>&copy; 2024. All rights reserved.</p>
            </div>
          </div>
        </footer>
      </div>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 0 0"
        width={0}
        height={0}
        focusable="false"
        role="none"
        style={{
          visibility: "hidden",
          position: "absolute",
          left: "-9999px",
          overflow: "hidden",
        }}
      >
        <defs>
          <filter id="duotone-grayscale">
            <feColorMatrix
              colorInterpolationFilters="sRGB"
              type="matrix"
              values=" .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 "
            ></feColorMatrix>
            <feComponentTransfer colorInterpolationFilters="sRGB">
              <feFuncR type="table" tableValues="0 1" />
              <feFuncG type="table" tableValues="0 1" />
              <feFuncB type="table" tableValues="0 1" />
              <feFuncA type="table" tableValues="1 1" />
            </feComponentTransfer>
            <feComposite in2="SourceGraphic" operator="in" />
          </filter>
        </defs>
      </svg>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 0 0"
        width={0}
        height={0}
        focusable="false"
        role="none"
        style={{
          visibility: "hidden",
          position: "absolute",
          left: "-9999px",
          overflow: "hidden",
        }}
      >
        <defs>
          <filter id="duotone-rgb106108108-ccc-1">
            <feColorMatrix
              colorInterpolationFilters="sRGB"
              type="matrix"
              values=" .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 "
            ></feColorMatrix>
            <feComponentTransfer colorInterpolationFilters="sRGB">
              <feFuncR type="table" tableValues="0.4156862745098 0.8" />
              <feFuncG type="table" tableValues="0.42352941176471 0.8" />
              <feFuncB type="table" tableValues="0.42352941176471 0.8" />
              <feFuncA type="table" tableValues="1 1" />
            </feComponentTransfer>
            <feComposite in2="SourceGraphic" operator="in" />
          </filter>
        </defs>
      </svg>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 0 0"
        width={0}
        height={0}
        focusable="false"
        role="none"
        style={{
          visibility: "hidden",
          position: "absolute",
          left: "-9999px",
          overflow: "hidden",
        }}
      >
        <defs>
          <filter id="duotone-rgb106108108-ccc-2">
            <feColorMatrix
              colorInterpolationFilters="sRGB"
              type="matrix"
              values=" .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 "
            ></feColorMatrix>
            <feComponentTransfer colorInterpolationFilters="sRGB">
              <feFuncR type="table" tableValues="0.4156862745098 0.8" />
              <feFuncG type="table" tableValues="0.42352941176471 0.8" />
              <feFuncB type="table" tableValues="0.42352941176471 0.8" />
              <feFuncA type="table" tableValues="1 1" />
            </feComponentTransfer>
            <feComposite in2="SourceGraphic" operator="in" />
          </filter>
        </defs>
      </svg>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 0 0"
        width={0}
        height={0}
        focusable="false"
        role="none"
        style={{
          visibility: "hidden",
          position: "absolute",
          left: "-9999px",
          overflow: "hidden",
        }}
      >
        <defs>
          <filter id="duotone-rgb106108108-ccc-3">
            <feColorMatrix
              colorInterpolationFilters="sRGB"
              type="matrix"
              values=" .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 "
            ></feColorMatrix>
            <feComponentTransfer colorInterpolationFilters="sRGB">
              <feFuncR type="table" tableValues="0.4156862745098 0.8" />
              <feFuncG type="table" tableValues="0.42352941176471 0.8" />
              <feFuncB type="table" tableValues="0.42352941176471 0.8" />
              <feFuncA type="table" tableValues="1 1" />
            </feComponentTransfer>
            <feComposite in2="SourceGraphic" operator="in" />
          </filter>
        </defs>
      </svg>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 0 0"
        width={0}
        height={0}
        focusable="false"
        role="none"
        style={{
          visibility: "hidden",
          position: "absolute",
          left: "-9999px",
          overflow: "hidden",
        }}
      >
        <defs>
          <filter id="duotone-rgb106108108-ccc-4">
            <feColorMatrix
              colorInterpolationFilters="sRGB"
              type="matrix"
              values=" .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 "
            ></feColorMatrix>
            <feComponentTransfer colorInterpolationFilters="sRGB">
              <feFuncR type="table" tableValues="0.4156862745098 0.8" />
              <feFuncG type="table" tableValues="0.42352941176471 0.8" />
              <feFuncB type="table" tableValues="0.42352941176471 0.8" />
              <feFuncA type="table" tableValues="1 1" />
            </feComponentTransfer>
            <feComposite in2="SourceGraphic" operator="in" />
          </filter>
        </defs>
      </svg>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 0 0"
        width={0}
        height={0}
        focusable="false"
        role="none"
        style={{
          visibility: "hidden",
          position: "absolute",
          left: "-9999px",
          overflow: "hidden",
        }}
      >
        <defs>
          <filter id="duotone-rgb106108108-ccc-5">
            <feColorMatrix
              colorInterpolationFilters="sRGB"
              type="matrix"
              values=" .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 "
            ></feColorMatrix>
            <feComponentTransfer colorInterpolationFilters="sRGB">
              <feFuncR type="table" tableValues="0.4156862745098 0.8" />
              <feFuncG type="table" tableValues="0.42352941176471 0.8" />
              <feFuncB type="table" tableValues="0.42352941176471 0.8" />
              <feFuncA type="table" tableValues="1 1" />
            </feComponentTransfer>
            <feComposite in2="SourceGraphic" operator="in" />
          </filter>
        </defs>
      </svg>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 0 0"
        width={0}
        height={0}
        focusable="false"
        role="none"
        style={{
          visibility: "hidden",
          position: "absolute",
          left: "-9999px",
          overflow: "hidden",
        }}
      >
        <defs>
          <filter id="duotone-rgb106108108-ccc-6">
            <feColorMatrix
              colorInterpolationFilters="sRGB"
              type="matrix"
              values=" .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 "
            ></feColorMatrix>
            <feComponentTransfer colorInterpolationFilters="sRGB">
              <feFuncR type="table" tableValues="0.4156862745098 0.8" />
              <feFuncG type="table" tableValues="0.42352941176471 0.8" />
              <feFuncB type="table" tableValues="0.42352941176471 0.8" />
              <feFuncA type="table" tableValues="1 1" />
            </feComponentTransfer>
            <feComposite in2="SourceGraphic" operator="in" />
          </filter>
        </defs>
      </svg>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 0 0"
        width={0}
        height={0}
        focusable="false"
        role="none"
        style={{
          visibility: "hidden",
          position: "absolute",
          left: "-9999px",
          overflow: "hidden",
        }}
      >
        <defs>
          <filter id="duotone-rgb224234255-rgb255255255-7">
            <feColorMatrix
              colorInterpolationFilters="sRGB"
              type="matrix"
              values=" .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 "
            ></feColorMatrix>
            <feComponentTransfer colorInterpolationFilters="sRGB">
              <feFuncR type="table" tableValues="0.87843137254902 1" />
              <feFuncG type="table" tableValues="0.91764705882353 1" />
              <feFuncB type="table" tableValues="1 1" />
              <feFuncA type="table" tableValues="1 1" />
            </feComponentTransfer>
            <feComposite in2="SourceGraphic" operator="in" />
          </filter>
        </defs>
      </svg>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 0 0"
        width={0}
        height={0}
        focusable="false"
        role="none"
        style={{
          visibility: "hidden",
          position: "absolute",
          left: "-9999px",
          overflow: "hidden",
        }}
      >
        <defs>
          <filter id="duotone-rgb224234255-rgb254254254-8">
            <feColorMatrix
              colorInterpolationFilters="sRGB"
              type="matrix"
              values=" .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 "
            ></feColorMatrix>
            <feComponentTransfer colorInterpolationFilters="sRGB">
              <feFuncR
                type="table"
                tableValues="0.87843137254902 0.99607843137255"
              />
              <feFuncG
                type="table"
                tableValues="0.91764705882353 0.99607843137255"
              />
              <feFuncB type="table" tableValues="1 0.99607843137255" />
              <feFuncA type="table" tableValues="1 1" />
            </feComponentTransfer>
            <feComposite in2="SourceGraphic" operator="in" />
          </filter>
        </defs>
      </svg>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 0 0"
        width={0}
        height={0}
        focusable="false"
        role="none"
        style={{
          visibility: "hidden",
          position: "absolute",
          left: "-9999px",
          overflow: "hidden",
        }}
      >
        <defs>
          <filter id="duotone-rgb224234255-rgb255254254-9">
            <feColorMatrix
              colorInterpolationFilters="sRGB"
              type="matrix"
              values=" .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 "
            ></feColorMatrix>
            <feComponentTransfer colorInterpolationFilters="sRGB">
              <feFuncR type="table" tableValues="0.87843137254902 1" />
              <feFuncG
                type="table"
                tableValues="0.91764705882353 0.99607843137255"
              />
              <feFuncB type="table" tableValues="1 0.99607843137255" />
              <feFuncA type="table" tableValues="1 1" />
            </feComponentTransfer>
            <feComposite in2="SourceGraphic" operator="in" />
          </filter>
        </defs>
      </svg>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 0 0"
        width={0}
        height={0}
        focusable="false"
        role="none"
        style={{
          visibility: "hidden",
          position: "absolute",
          left: "-9999px",
          overflow: "hidden",
        }}
      >
        <defs>
          <filter id="duotone-rgb224234255-rgb255255255-10">
            <feColorMatrix
              colorInterpolationFilters="sRGB"
              type="matrix"
              values=" .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 .299 .587 .114 0 0 "
            ></feColorMatrix>
            <feComponentTransfer colorInterpolationFilters="sRGB">
              <feFuncR type="table" tableValues="0.87843137254902 1" />
              <feFuncG type="table" tableValues="0.91764705882353 1" />
              <feFuncB type="table" tableValues="1 1" />
              <feFuncA type="table" tableValues="1 1" />
            </feComponentTransfer>
            <feComposite in2="SourceGraphic" operator="in" />
          </filter>
        </defs>
      </svg>
      <script
        src="/landing-page/js/animation-script.js?ver=1.0.1"
        id="animation-script-js"
      ></script>
      <script
        src="/landing-page/js/block-template-skip-link.js"
        id="block-template-skip-link-js-after"
      ></script>
    </div>
  );
}
