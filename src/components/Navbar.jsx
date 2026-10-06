import { Link } from "react-router";

const Navbar = () => {
  const menu = (
    <>
      <li>
        <Link
          to="/how-it-works"
          className="btn btn-link text-black font-semibold"
        >
          How It Works
        </Link>
      </li>
      <li>
        <button className="btn btn-soft border border-black/20 font-semibold">
          বাংলা / English
        </button>
      </li>
      <li>
        <button className="btn bg-green-900 text-center text-white font-semibold">
          Start Planning
        </button>
      </li>
    </>
  );
  return (
    <div className="navbar bg-[#FBF9F5] shadow-sm">
      <div className="max-w-9/12 mx-auto flex w-full items-center max-lg:max-w-10/12 max-md:max-w-11/12">
        <div className="flex-1">
          <Link to={"/"} className="text-xl font-bold">
            ফসল-Cycle
          </Link>
        </div>
        <div className="flex-none">
          <ul className="menu items-center gap-4 menu-horizontal">{menu}</ul>
        </div>
      </div>
    </div>
  );
};

export default Navbar;
