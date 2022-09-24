function [ u, it_num ] = monogrid_poisson_1d ( n, a, b, ua, ub, force, exact )

%*****************************************************************************80
%                                                    
%% monogrid_poisson_1d() solves a 1D PDE, using the Gauss-Seidel method.
%
%  Discussion:
%
%    This routine solves a 1D boundary value problem of the form
%
%      - U''(X) = F(X) for A < X < B,
%
%    with boundary conditions U(A) = UA, U(B) = UB.
%
%    The Gauss-Seidel method is used. 
%
%    This routine is provided primarily for comparison with the
%    multigrid solver.
%
%  Licensing:
%
%    This code is distributed under the GNU LGPL license.
%
%  Modified:
%
%    26 July 2014
%
%  Author:
%
%    John Burkardt
%
%  Reference:
%
%    William Hager,
%    Applied Numerical Linear Algebra,
%    Prentice-Hall, 1988,
%    ISBN13: 978-0130412942,
%    LC: QA184.H33.
%
%  Input:
%
%    integer N, the number of intervals.
%
%    real A, B, the left and right endpoints of the region.
%
%    real UA, UB, the left and right boundary values.
%
%    function value = FORCE ( x ), the name of the function 
%    which evaluates the right hand side.
%
%    function value = EXACT ( x ), the name of the function 
%    which evaluates the exact solution.
%
%  Output:
%
%    integer IT_NUM, the number of iterations.
%
%    real U(N+1,1), the computed solution.
%

%
%  Initialization.
%
  tol = 0.0001;
%
%  Set the nodes.
%
  x = ( linspace ( a, b, n + 1 ) )';
%
%  Set the right hand side.
%
  r = zeros ( n + 1, 1 );

  r(1) = ua;
  r(2:n) = force ( x(2:n) ) / n / n;
  r(n+1) = ub;

  u = zeros ( n + 1, 1 );

  it_num = 0;
%
%  Gauss-Seidel iteration.
%
  while ( true )

    it_num = it_num + 1;

    [ u, d1 ] = gauss_seidel ( n + 1, r, u );

    if ( d1 <= tol )
      break
    end

  end

  return
end
